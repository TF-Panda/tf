#include "server.h"
#include "datagramIterator.h"
#include "steamnet_includes.h"

#ifdef SERVER

#include "notifyCategoryProxy.h"
#include "pandabase.h"
#include "steamNetworkConnectionInfo.h"
#include "steamNetworkMessage.h"
#include "../netMessages.h"
#include "../networkClass.h"

GameServer *GameServer::_global_ptr = nullptr;

NotifyCategoryDeclNoExport(server);
NotifyCategoryDef(server, "tf");

ConfigVariableInt sv_min_update_rate
("sv-min-update-rate", 20,
 PRC_DESC("Minimum rate clients can request snapshots from the server."));
ConfigVariableInt sv_max_update_rate
("sv-max-update-rate", 100,
 PRC_DESC("Maximum rate clients can request snapshots from the server."));
ConfigVariableInt sv_max_clients
("sv-max-clients", 24,
 PRC_DESC("Maximum number of client connections/concurrent players."));

/**
 *
 */
GameServer::
GameServer() :
  _net_sys(SteamNetworkSystem::get_global_ptr()),
  _next_do_id(1u),
  _next_client_id(1),
  _num_clients(0),
  _client_sender(nullptr),
  _poll_group(INVALID_STEAM_NETWORK_POLL_GROUP_HANDLE),
  _listen_socket(INVALID_STEAM_NETWORK_CONNECTION_HANDLE),
  _max_clients(sv_max_clients)
{
}

/**
 *
 */
void
GameServer::startup(int port) {
  _listen_socket = _net_sys->create_listen_socket(port);
  _poll_group = _net_sys->create_poll_group();
  server_cat.info() << "Server opened on port " << port << "\n";
}

/**
 *
 */
void
GameServer::handle_message(SteamNetworkMessage *msg) {
  SteamNetworkConnectionHandle conn = msg->get_connection();
  DatagramIterator &scan = msg->get_datagram_iterator();

  auto it = _client_connections.find(conn);
  if (it == _client_connections.end()) {
    // Don't know this client?
    server_cat.warning() << "Received message from unknown connection " << conn
                         << "\n";
    return;
  }

  ClientConnection *client = (*it).second;

  NetMessages::MessageType msg_type = (NetMessages::MessageType)scan.get_uint16();

  if (client->state == ClientConnection::CS_unverified) {
    // Expect a hello.
    if (msg_type == NetMessages::CL_hello) {
      handle_client_hello(client, scan);
    } else {
      server_cat.warning()
          << "Client " << conn
          << " sent something other than hello in unverified state\n";
      close_client_connection(client);
    }

  } else if (client->state == ClientConnection::CS_verified) {
    switch (msg_type) {
    case NetMessages::B_object_message:
      handle_object_message(client, scan);
      break;
    case NetMessages::CL_world_update_ack:
      handle_client_tick(client, scan);
      break;
    default:
      break;
    }
  }
}

/**
 *
 */
void GameServer::
handle_client_hello(ClientConnection *client, DatagramIterator &scan) {
  // Must have 2 byte string length for password.
  if (!ensure_datagram_size(2u, scan, client)) {
    return;
  }
  std::string password = scan.get_string();

  int update_rate = scan.get_uint8();
  int cmd_rate = scan.get_uint8();
  float interp_amount = scan.get_float32();

  Datagram dg;
  dg.add_uint16(NetMessages::SV_hello_resp);

  bool valid = true;
  std::string msg = "";

  if (_num_clients >= _max_clients) {
    // Server is full.
    valid = false;
    msg = "Server is full.";
  } else if (client->state == ClientConnection::CS_verified) {
    valid = false;
    msg = "Already signed in.";
  }

  dg.add_bool(valid);
  if (!valid) {
    server_cat.warning()
      << "Could not verify client " << client->connection << " (" << msg << ")\n";
    dg.add_string(msg);
    send_datagram(dg, client->connection);
    close_client_connection(client);
    return;
  }

  // Make sure the client's requested snapshot rate is
  // within our defined boundaries.
  update_rate = std::max(sv_min_update_rate.get_value(), std::min(sv_max_update_rate.get_value(), update_rate));
  client->update_rate = update_rate;
  client->update_interval = 1.0f / (float)update_rate;
  client->interp_amount = interp_amount;

  client->cmd_rate = cmd_rate;
  client->cmd_interval = 1.0f / (float)cmd_rate;

  if (true) { // do we want authentication?
    client->state = ClientConnection::CS_verified;
    client->id = _next_client_id++;

    server_cat.info()
      << "Got hello from client " << client->connection << ", verified, given ID " << client->id << "\n";
    server_cat.info()
      << "Client lerp time: " << interp_amount << "\n";

    // Tell the client their ID, our tick rate, and their clamped snapshot rate.
    dg.add_bool(false);
    dg.add_uint16(client->id);
    dg.add_uint8(_tick_rate);
    dg.add_uint32(_tick_count);
    dg.add_uint8(update_rate);

    ++_num_clients;

    send_datagram(dg, client->connection);

    // Now give them interest into the "game manager zone".
    add_client_interest(client, { game_manager_zone });

  } else {
    // We would do authentication here.
  }
}

/**
 *
 */
void GameServer::
handle_client_tick(ClientConnection *client, DatagramIterator &scan) {
  if (!ensure_datagram_size(4u, scan, client)) {
    return;
  }
  client->delta_tick = scan.get_int32();
}

/**
 * Handles a networked object RPC from a client.
 */
void GameServer::
handle_object_message(ClientConnection *client, DatagramIterator &scan) {
  DO_ID doid = scan.get_uint32();
  uint16_t rpc_number = scan.get_uint16();
  ObjectsByID::const_iterator it = _doid2do.find(doid);
  if (it == _doid2do.end()) {
    server_cat.warning()
      << "Received RPC from client " << client->connection << " for unknown DO ID " << doid << "\n";
    return;
  }
  NetworkObject *obj = (*it).second;

  ZONE_ID zoneid = obj->get_zone_id();
  if (!client->has_interest(zoneid)) {
    // Client doesn't have interest in the object's zone, they shouldn't have been able
    // to send this.  Ignore the RPC.
    return;
  }

  NetworkClass *net_class = obj->get_network_class();
  NetworkRPC *rpc = net_class->get_inherited_rpc(rpc_number);
  if (rpc == nullptr) {
    server_cat.warning()
      << "RPC " << rpc_number << " sent from client " << client->connection << " does not exist on net class " << net_class->get_name() << "\n";
    return;
  }

  if (obj->get_owner() != client) {
    if ((rpc->flags & NetworkRPC::F_clsend) == 0) {
      // This client doesn't own the object and the RPC isn't marked clsend.
      // They aren't allowed to send it.
      return;
    }
  } else {
    if ((rpc->flags & (NetworkRPC::F_ownsend | NetworkRPC::F_clsend)) == 0) {
      // Client owns object but the field isn't ownsend or clsend, so they
      // can't send it.
      return;
    }
  }

  // Store off client that sent this RPC so the procedure can reply if necessary.
  _client_sender = client;
  // Read message args and invoke the procedure on the object.
  rpc->read(scan, obj);
  _client_sender = nullptr;
}

/**
 * Ensures that the given datagram has at least size bytes remaining.  If not,
 * disconnects the client.
 */
bool
GameServer::ensure_datagram_size(size_t size, DatagramIterator &scan,
                             ClientConnection *client) {
  if (scan.get_remaining_size() < size) {
    server_cat.warning() << "Truncated message from client "
                         << client->connection << "\n";
    close_client_connection(client);
    return false;
  }
  return true;
}

/**
 *
 */
void
GameServer::handle_net_callback(SteamNetworkEvent *event) {
  switch (event->get_state()) {
  case SteamNetworkEnums::NCS_connecting:
    // New client.
    handle_connecting_client(event->get_connection());
    break;
  case SteamNetworkEnums::NCS_closed_by_peer:
  case SteamNetworkEnums::NCS_problem_detected_locally:
    // Disconnected client.
    {
      auto it = _client_connections.find(event->get_connection());
      if (it == _client_connections.end()) {
        server_cat.info() << "Connection " << event->get_connection()
                          << " disconnected"
                          << "but wasn't a recorded client, ignoring\n";
	return;
      }
      server_cat.info() << "Client " << event->get_connection()
                        << " disconnected\n";
      handle_disconnecting_client((*it).second);
    }
    break;
  default:
    break;
  }
}

/**
 * Handles a client requesting to connect to the server.
 * If the connection is accepted, server needs client to send
 * a hello message before they can be spawned in.
 */
void GameServer::
handle_connecting_client(SteamNetworkConnectionHandle conn) {
  auto it = _client_connections.find(conn);
  if (it != _client_connections.end()) {
    // Weird.
    server_cat.warning() << "Connection " << conn << " already connected?\n";
    return;
  }

  if (!can_accept_connection()) {
    return;
  }

  if (!_net_sys->accept_connection(conn)) {
    server_cat.warning() << "Couldn't accept connection " << conn << "\n";
    return;
  }

  if (!_net_sys->set_connection_poll_group(conn, _poll_group)) {
    server_cat.warning() << "Couldn't set poll group on connection " << conn
                         << "\n";
    _net_sys->close_connection(conn);
    return;
  }



  SteamNetworkConnectionInfo info;
  _net_sys->get_connection_info(conn, &info);

  server_cat.info()
    << "Got new connection " << conn << " at  " << info.get_net_address() << "\n";

  PT(ClientConnection) client = new ClientConnection;
  client->connection = conn;
  client->address = info.get_net_address();
  client->id = -1;
  // We need a hello message from the client.
  client->state = ClientConnection::CS_unverified;
  _client_connections.insert({conn, client});
}

/**
 * Handles a client that is disconnecting from the server, for any reason
 * (manual disconnect, lost connection, etc).
 */
void
GameServer::handle_disconnecting_client(ClientConnection *client) {
  close_client_connection(client);
}

/**
 *
 */
void
GameServer::close_client_connection(ClientConnection *client) {
  // Delete all client owned objects.
  for (ClientConnection::ObjectsByDoID::const_iterator it =
           client->objects_by_do_id.begin();
       it != client->objects_by_do_id.end(); ++it) {
    NetworkObject *obj = (*it).second;
    delete_object(obj);
  }
  client->objects_by_do_id.clear();

  if (client->state == ClientConnection::CS_verified) {
    // Only verified clients count towards player/client count.
    --_num_clients;
  }

  _net_sys->close_connection(client->connection);

  // Remove from client table.
  auto it = _client_connections.find(client->connection);
  nassertv(it != _client_connections.end());
  _client_connections.erase(it);
}

/**
 * Gives the client interest in the given network zones.
 */
void GameServer::
add_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones) {
  pset<ZONE_ID> new_zones = client->interest_zones;
  for (ZONE_ID zone : zones) {
    new_zones.insert(zone);
  }
  update_client_interest(client, new_zones);
}

/**
 *
 */
void GameServer::
remove_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones) {
  pset<ZONE_ID> new_zones = client->interest_zones;
  for (ZONE_ID zone : zones) {
    new_zones.erase(zone);
  }
  update_client_interest(client, new_zones);
}

/**
 *
 */
void GameServer::
update_client_interest(ClientConnection *client, const pset<ZONE_ID> &zones) {
  // Send deletes for objects in zones client is removing interest from.
  Datagram dg;
  dg.add_uint16(NetMessages::SV_delete_object);
  int num_removed_objects = 0;
  for (ZONE_ID zone : client->interest_zones) {
    if (zones.find(zone) != zones.end()) {
      // Zone wasn't removed, nothing to do.
      continue;
    }

    ObjectsByZoneID::const_iterator it = _zoneid2do.find(zone);
    if (it == _zoneid2do.end()) {
      continue;
    }

    const ObjectSet &objects = (*it).second;
    if (objects.empty()) {
      continue;
    }

    for (NetworkObject *obj : objects) {
      dg.add_uint32(obj->get_do_id());
      ++num_removed_objects;
    }
  }

  if (num_removed_objects > 0) {
    send_datagram(dg, client->connection);
  }

  dg.clear();

  // Send generates for objects in zones client is adding interest to.
  dg.add_uint16(NetMessages::SV_generate_object);
  int num_generated_objects = 0;
  for (ZONE_ID zone_id : zones) {
    if (client->has_interest(zone_id)) {
      // We already have interest in this zone, nothing to do.
      continue;
    }

    ObjectsByZoneID::const_iterator it = _zoneid2do.find(zone_id);
    if (it == _zoneid2do.end()) {
      continue;
    }

    const ObjectSet &objects = (*it).second;
    if (objects.empty()) {
      continue;
    }

    for (NetworkObject *obj : objects) {
      if (obj->get_owner() == client) {
	// Don't send it to them if they own it.  It should already be generated for them.
	continue;
      }
      pack_object_generate(dg, obj, false);
      ++num_generated_objects;
    }
  }

  if (num_generated_objects > 0) {
    send_datagram(dg, client->connection);
  }

  // Store off new interest zones.
  client->interest_zones = zones;
}

/**
 * Starts replicating a networked object to all clients with interest in
 * the given network zone.  Optionally, the object can be given an "owner"
 * client, which may give the client special priviledges over the object.
 */
void GameServer::
generate_object(NetworkObject *obj, ZONE_ID zone_id, ClientConnection *owner) {
  nassertv(obj->is_do_new()); // Shouldn't be calling generate_object() more than once.

  obj->set_zone_id(zone_id);
  obj->set_owner(owner);
  obj->set_do_id(_next_do_id++);

  obj->pre_generate();

  // Add to tables.
  _doid2do.insert({ obj->get_do_id(), obj });
  ObjectsByZoneID::iterator it = _zoneid2do.find(zone_id);
  if (it == _zoneid2do.end()) {
    _zoneid2do.insert({ zone_id, { obj }});
  } else {
    (*it).second.insert(obj);
  }
  if (owner != nullptr) {
    owner->objects_by_do_id.insert({ obj->get_do_id(), obj });
  }

  // Send object out to clients.
  Datagram dg;
  dg.add_uint16(NetMessages::SV_generate_object);
  pack_object_generate(dg, obj, false);
  for (auto client_entry : _client_connections) {
    ClientConnection *client = client_entry.second;
    if (client->has_interest(obj->get_zone_id()) && client != owner) {
      // Client has interest in zone of the object, send it to them.
      send_datagram(dg, client->connection);
    }
  }

  if (owner != nullptr) {
    // Send a special generate for the owner.
    dg.clear();

    dg.add_uint16(NetMessages::SV_generate_object);
    pack_object_generate(dg, obj, true);
    send_datagram(dg, owner->connection);

    // Follow interest system.  Client implicitly has interest in the
    // location of owned objects.
    add_client_interest(owner, { zone_id });
  }

  // Make the object alive.
  obj->generate();

  nassertv(obj->is_do_alive());
}

/**
 *
 */
void GameServer::
delete_object(NetworkObject *obj) {
  nassertv(obj->is_do_alive());

  DO_ID doid = obj->get_do_id();

  // Remove from zone id table.
  auto zone_it = _zoneid2do.find(obj->get_zone_id());
  if (zone_it != _zoneid2do.end()) {
    auto zone_obj_it = zone_it->second.find(obj);
    if (zone_obj_it != zone_it->second.end()) {
      zone_it->second.erase(zone_obj_it);
    }
  }

  ClientConnection *owner = obj->get_owner();
  if (owner != nullptr) {
    // Also remove the object from the owner's table.
    auto owner_it = owner->objects_by_do_id.find(doid);
    if (owner_it != owner->objects_by_do_id.end()) {
      owner->objects_by_do_id.erase(owner_it);
    }
  }

  // Inform any clients that see the object.
  Datagram dg;
  dg.add_uint16(NetMessages::SV_delete_object);
  dg.add_uint32(doid);
  for (auto client_entry : _client_connections) {
    ClientConnection *client = client_entry.second;
    if (client->has_interest(obj->get_zone_id())) {
      send_datagram(dg, client->connection);
    }
  }

  // Forget this object in the packet history.
  _snapshot_mgr.remove_prev_sent_packet(doid);

  obj->disable();
  nassertv(obj->is_do_disabled());

  // Remove from main object table.
  // Should drop last reference to the object.
  auto it = _doid2do.find(doid);
  if (it != _doid2do.end()) {
    _doid2do.erase(it);
  }
}

/**
 * Sends the datagram to the given client.
 */
void GameServer::
send_datagram(const Datagram &dg, SteamNetworkConnectionHandle conn, bool reliable) {
  SteamNetworkEnums::NetworkSendFlags flags;
  if (!reliable) {
    flags = SteamNetworkEnums::NSF_unreliable_no_delay;
  } else {
    flags = SteamNetworkEnums::NSF_reliable_no_nagle;
  }
  _net_sys->send_datagram(conn, dg, flags);
}

/**
 *
 */
void
GameServer::run_simulation() {
  // Process incoming messages.

  SteamNetworkMessage msg;
  while (_net_sys->receive_message_on_poll_group(_poll_group, msg)) {
    handle_message(&msg);
  }

  // Run and process network system callbacks.
  _net_sys->run_callbacks();

  PT(SteamNetworkEvent) event = _net_sys->get_next_event();
  while (event != nullptr) {
    handle_net_callback(event);
    event = _net_sys->get_next_event();
  }
}

/**
 *
 */
void GameServer::
post_simulate() {
  take_tick_snapshot(get_tick_count());
}


/**
 *
 */
bool
GameServer::can_accept_connection() const {
  return true;
}

/**
 * For an object generate message, writes the data for a single object
 * to be generated.
 */
void GameServer::
pack_object_generate(Datagram &dg, NetworkObject *obj, bool owner) {
  dg.add_bool(owner);
  dg.add_uint16(obj->get_network_class()->get_id());
  dg.add_uint32(obj->get_do_id());
  dg.add_uint32(obj->get_zone_id());

  // See if we have a baseline state to send already.
  PackedObject *baseline = _snapshot_mgr.get_baseline_object_state(obj, obj->get_network_class(), obj->get_do_id());
  if (baseline != nullptr) {
    // We got a baseline, pack it into the datagram.
    dg.add_bool(true);
    baseline->pack_datagram(dg);
  } else {
    // No initial state for object?
    dg.add_bool(false);
  }
}

/**
 *
 */
void GameServer::
take_tick_snapshot(int tick_count) {
  float time = get_time();

  // Don't make a snapshot unless at least once client actually
  // needs one.
  pvector<ClientConnection *> clients_needing_update;
  pset<ZONE_ID> client_zones;
  clients_needing_update.reserve(_client_connections.size());
  for (auto client_entry : _client_connections) {
    ClientConnection *client = client_entry.second;
    if (client->next_update_time <= time) {
      // Time for an update!
      // Factor in their interest zones for the complete
      // set of zones we need to snapshot for all clients.
      for (ZONE_ID zone : client->interest_zones) {
	client_zones.insert(zone);
      }
      // Note their next update time.
      client->next_update_time = time + client->update_interval;
      clients_needing_update.push_back(client);
    }
  }

  if (clients_needing_update.empty()) {
    // No clients need an update, don't need to do anything.
    return;
  }

  PT(FrameSnapshot) snap = new FrameSnapshot;
  snap->tick = tick_count;
  snap->entries.resize(_doid2do.size());
  snap->valid_entries.reserve(_doid2do.size());

  int entry_number = 0;

  for (auto obj_entry : _doid2do) {
    DO_ID doid = obj_entry.first;
    NetworkObject *obj = obj_entry.second;
    if (client_zones.find(obj->get_zone_id()) == client_zones.end()) {
      // Object isn't in any of the zones our clients needing updates have interest in.
      // Exclude it.
      ++entry_number;
      continue;
    }

    NetworkClass *net_class = obj->get_network_class();

    // Pack it in!
    _snapshot_mgr.pack_object_in_snapshot(snap, entry_number, obj, doid,
					  obj->get_zone_id(), net_class);

    ++entry_number;
  }

  Datagram dg;

  // Send it out to whoever needs it.
  for (ClientConnection *client : clients_needing_update) {
    const ClientFrame *old_frame = client->get_client_frame(client->delta_tick);

    // Keep track of the snapshot we sent for this client to delta against it
    // next update.
    ClientFrame new_frame;
    new_frame.snapshot = snap;
    new_frame.tick = tick_count;

    dg.clear();
    dg.add_uint16(NetMessages::SV_world_update);
    if (old_frame != nullptr) {
      // We have an old frame to delta against.
      _snapshot_mgr.client_format_delta_snapshot(dg, old_frame->snapshot, snap, client->interest_zones);
    } else {
      // Pack full state.
      _snapshot_mgr.client_format_snapshot(dg, snap, client->interest_zones);
    }

    // Send it out to them!
    // It doesn't need to be reliable.
    send_datagram(dg, client->connection, false);

    // Store off the new frame.
    client->frame_list.add_client_frame(new_frame);
  }
}

/**
 * Sends an RPC for the given networked object.  Can optionally target a specific client.
 * If the field is broadcast, can optionally exclude specific clients from receiving the RPC.
 */
void GameServer::
send_obj_message(NetworkObject *obj, const std::string &msg_name, void *msg_args, ClientConnection *client, const pvector<ClientConnection *> &exclude_clients) {
  if (obj == nullptr) {
    return;
  }
  NetworkClass *net_class = obj->get_network_class();
  if (net_class == nullptr) {
    return;
  }

  NetworkRPC *rpc = nullptr;
  int rpc_index = -1;
  for (int i = net_class->get_num_inherited_rpcs() - 1; i >= 0; --i) {
    NetworkRPC *test_rpc = net_class->get_inherited_rpc((size_t)i);
    if (test_rpc->name == msg_name) {
      rpc_index = i;
      rpc = test_rpc;
      break;
    }
  }

  if (rpc == nullptr) {
    server_cat.warning()
      << "No RPC/message named " << msg_name << " on NetworkClass " << net_class->get_name() << "\n";
    return;
  }

  Datagram dg;
  dg.add_uint16(NetMessages::B_object_message);
  dg.add_uint32(obj->get_do_id());
  dg.add_uint16(rpc_index);

  // Pack RPC args into datagram.
  rpc->write(dg, msg_args);

  bool reliable = (rpc->flags & NetworkRPC::F_unreliable) == 0;

  if (client != nullptr) {
    // We're targetting the RPC to a specific client.
    send_datagram(dg, client->connection, reliable);

  } else {
    // Follow behavior from RPC flags.
    if ((rpc->flags & NetworkRPC::F_broadcast) != 0) {
      // Send to all interested clients.
      for (auto client_entry : _client_connections) {
	ClientConnection *client = client_entry.second;
	if (client->has_interest(obj->get_zone_id())) {
	  if (std::find(exclude_clients.begin(), exclude_clients.end(), client) == exclude_clients.end()) {
	    send_datagram(dg, client->connection, reliable);
	  }
	}
      }

    } else if ((rpc->flags & NetworkRPC::F_ownrecv) != 0) {
      // If the field is an ownrecv without an explicit target client,
      // implicitly send to owner client.
      ClientConnection *owner = obj->get_owner();
      if (owner == nullptr) {
	server_cat.warning()
	  << "Can't implicitly send ownrecv message to owner with no owner client\n";
	return;
      }
      send_datagram(dg, owner->connection, reliable);

    } else {
      server_cat.warning()
	<< "Can't send non-broadcast and non-ownrecv object message without a target client\n";
    }
  }
}

#endif  // SERVER

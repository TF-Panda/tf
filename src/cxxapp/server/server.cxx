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

Server *Server::_global_ptr = nullptr;

NotifyCategoryDeclNoExport(server);
NotifyCategoryDef(server, "tf");

ConfigVariableInt sv_min_update_rate
("sv-min-update-rate", 20,
 PRC_DESC("Minimum rate clients can request snapshots from the server."));
ConfigVariableInt sv_max_update_rate
("sv-max-update-rate", 100,
 PRC_DESC("Maximum rate clients can request snapshots from the server."));

/**
 *
 */
Server::
Server() :
  _net_sys(SteamNetworkSystem::get_global_ptr()),
  _next_do_id(1u),
  _num_clients(0)
{
}

/**
 *
 */
void
Server::startup(int port) {
  _listen_socket = _net_sys->create_listen_socket(port);
  _poll_group = _net_sys->create_poll_group();
  server_cat.info() << "Server opened on port " << port << "\n";
}

/**
 *
 */
void
Server::handle_message(SteamNetworkMessage *msg) {
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

  }
}

/**
 *
 */
void Server::
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

  if (client->state == ClientConnection::CS_verified) {
    valid = false;
    msg = "Already signed in.\n";
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
    client->id = 1;

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

  } else {
    // We would do authentication here.
  }
}

/**
 * Ensures that the given datagram has at least size bytes remaining.  If not,
 * disconnects the client.
 */
bool
Server::ensure_datagram_size(size_t size, DatagramIterator &scan,
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
Server::handle_net_callback(SteamNetworkEvent *event) {
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
void Server::
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
Server::handle_disconnecting_client(ClientConnection *client) {
  close_client_connection(client);
}

/**
 *
 */
void
Server::close_client_connection(ClientConnection *client) {
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
void Server::
add_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones) {
  pset<ZONE_ID> new_zones = client->_interest_zones;
  for (ZONE_ID zone : zones) {
    new_zones.insert(zone);
  }
  update_client_interest(client, new_zones);
}

/**
 *
 */
void Server::
remove_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones) {
  pset<ZONE_ID> new_zones = client->_interest_zones;
  for (ZONE_ID zone : zones) {
    new_zones.erase(zone);
  }
  update_client_interest(client, new_zones);
}

/**
 *
 */
void Server::
update_client_interest(ClientConnection *client, const pset<ZONE_ID> &zones) {
  // Send deletes for objects in zones client is removing interest from.
  Datagram dg;
  dg.add_uint16(NetMessages::SV_delete_object);
  int num_removed_objects = 0;
  for (ZONE_ID zone : client->_interest_zones) {
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
    if (client->_interest_zones.find(zone_id) != client->_interest_zones.end()) {
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
      NetworkClass *net_class = obj->get_network_class();
      dg.add_uint16(net_class->get_id());
      dg.add_uint32(obj->get_do_id());
      dg.add_uint32(obj->get_zone_id());

      bool has_state = false;
      dg.add_bool(has_state);

      ++num_generated_objects;
    }
  }

  if (num_generated_objects > 0) {
    send_datagram(dg, client->connection);
  }

  // Store off new interest zones.
  client->_interest_zones = zones;
}

/**
 *
 */
void Server::
generate_object(NetworkObject *obj, ZONE_ID zone_id, ClientConnection *owner) {
  nassertv(obj->is_do_new());
  obj->set_zone_id(zone_id);
  obj->set_owner(owner);
  obj->set_do_id(_next_do_id++);

  obj->pre_generate();
  obj->generate();

  nassertv(obj->is_do_alive());

  // Add to tables.
  _doid2do.insert({ obj->get_do_id(), obj });
  ObjectsByZoneID::iterator it = _zoneid2do.find(zone_id);
  if (it == _zoneid2do.end()) {
    _zoneid2do.insert({ zone_id, { obj }});
  } else {
    (*it).second.insert(obj);
  }

  // Send object out to clients.
  NetworkClass *net_class = obj->get_network_class();
  Datagram dg;
  dg.add_uint16(NetMessages::SV_generate_object);
  dg.add_uint16(net_class->get_id());
  dg.add_uint32(obj->get_do_id());
  dg.add_uint32(obj->get_zone_id());
  // Package up state.
  dg.add_bool(true);

  for (auto client_entry : _client_connections) {
    ClientConnection *client = client_entry.second;
    if (client->_interest_zones.find(zone_id) != client->_interest_zones.end()) {

    }
  }
}

/**
 * Sends the datagram to the given client.
 */
void Server::
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
Server::run_simulation() {
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
bool
Server::can_accept_connection() const {
  return true;
}

#endif  // SERVER

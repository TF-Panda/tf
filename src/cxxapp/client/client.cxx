#ifdef CLIENT

#include "client.h"
#include "pnotify.h"
#include "steamNetworkMessage.h"
#include "steamnet_includes.h"
#include "../netMessages.h"
#include "../networkClassRegistry.h"
#include "../networkClass.h"
#include "client_config.h"
#include "../gameGlobals.h"
#include "../tfPlayer.h"
#include "localTFPlayer.h"

NotifyCategoryDeclNoExport(client);
NotifyCategoryDef(client, "tf");

GameClient *GameClient::_ptr = nullptr;

/**
 *
 */
void
GameClient::try_connect(const NetAddress &addr, ConnectCallback callback) {
  _connect_callback = callback;
  client_cat.info() << "Attempting to connect to " << addr << "\n";
  _server_address = addr;
  _connection = _net_sys->connect_by_IP_address(addr);
  if (_connection == INVALID_STEAM_NETWORK_CONNECTION_HANDLE) {
    client_cat.warning() << "Immediate failure connecting to " << addr << "\n";
    if (_connect_callback != nullptr) {
      (*_connect_callback)(this, false, addr);
    }
    _server_address.clear();
  }
}

/**
 *
 */
void
GameClient::run_simulation() {
  if (_connection == INVALID_STEAM_NETWORK_CONNECTION_HANDLE) {
    // Nothing to do unless we have a connection to the server.
    return;
  }

  if (_connected) {
    // If we're connected to the server, read incoming messages.
    SteamNetworkMessage msg;
    while (_net_sys->receive_message_on_connection(_connection, msg)) {
      handle_message(&msg);
    }
  }

  // Process network events.  We run these even if not connected
  // as an event tells us if we connected successfully or not.
  _net_sys->run_callbacks();

  PT(SteamNetworkEvent) ev = _net_sys->get_next_event();
  while (ev != nullptr) {
    handle_event(ev);
    ev = _net_sys->get_next_event();
  }

  // Run player controls.
  LocalTFPlayer *local_player = globals.get_local_tf_player();
  if (local_player != nullptr) {
    local_player->run_controls();
  }
}

/**
 * Handles a message received from the server.
 */
void GameClient::
handle_message(SteamNetworkMessage *msg) {
  DatagramIterator &scan = msg->get_datagram_iterator();
  NetMessages::MessageType msg_type = (NetMessages::MessageType)scan.get_uint16();

  switch (msg_type) {
  case NetMessages::SV_hello_resp:
    handle_server_hello_resp(scan);
    break;
  case NetMessages::SV_generate_object:
    handle_generate_object(scan);
    break;
  case NetMessages::SV_delete_object:
    handle_delete_object(scan);
    break;
  case NetMessages::SV_world_update:
    handle_server_world_update(scan);
    break;
  case NetMessages::B_object_message:
    handle_object_message(scan);
    break;
  default:
    client_cat.warning() << "Don't know how to handle msg type " << msg_type
                         << " from server\n";
    break;
  }
}

/**
 *
 */
void
GameClient::handle_server_hello_resp(DatagramIterator &scan) {
  bool ret = scan.get_bool();

  if (ret) {
    bool want_auth = scan.get_bool();
    _client_id = scan.get_uint16();

    client_cat.info() << "Signed onto server\n";
    _server_tick_rate = scan.get_uint8();
    _server_tick_interval = 1.0f / _server_tick_rate;

    set_tick_rate(_server_tick_rate);
    int tick_count = scan.get_uint32();
    reset_simulation(tick_count);

    client_cat.info()
      << "Server tick count is " << _tick_count << ", tick rate " << _server_tick_rate << "\n";
    client_cat.info()
      << "My client id: " << _client_id << "\n";

    int update_rate = scan.get_uint8();
    cl_update_rate = update_rate;
    client_cat.info()
      << "my update rate: " << update_rate << "\n";

    if (_sign_on_callback != nullptr) {
      (*_sign_on_callback)(this, true, "");
    }

  } else {
    _disconnect_reason = scan.get_string();
    client_cat.warning() << "Failed to sign onto server: "  << _disconnect_reason << "\n";
    if (_sign_on_callback != nullptr) {
      (*_sign_on_callback)(this, false, _disconnect_reason);
    }
    disconnect();
  }
}

struct GeneratedObject {
  NetworkObject *obj;
  bool has_state;
};

/**
 *
 */
void GameClient::
handle_generate_object(DatagramIterator &scan) {
  NetworkClassRegistry *reg = NetworkClassRegistry::ptr();

  pvector<GeneratedObject> generated_objs;

  // Generate message can contain multiple objects.
  while (scan.get_remaining_size() > 0) {
    bool owner = scan.get_bool(); // Are we the owner of this object?
    uint16_t classid = scan.get_uint16();
    DO_ID doid = scan.get_uint32();
    ZONE_ID zoneid = scan.get_uint32();
    bool has_state = scan.get_bool();

    if (client_cat.is_debug()) {
      client_cat.debug()
	<< "Got generate for object, classid " << classid << ", doid " << doid << ", zone id " << zoneid << ", has initial state: " << has_state << "\n";
    }

    NetworkClass *net_class = reg->get_class_by_id(classid);
    nassertv(net_class != nullptr);

    if (net_class == nullptr) {
      client_cat.warning()
        << "Received generate for unknown class id: " << classid << "\n";
        return;
    }

    NetworkClass::EntityFactoryFunc factory = net_class->get_factory_func();
    nassertv(factory != nullptr);

    PT(NetworkObject) obj = (*factory)();
    obj->set_do_id(doid);
    obj->set_zone_id(zoneid);
    obj->set_owner(owner);
    _doid2do.insert({ doid, obj });

    obj->pre_generate();

    GeneratedObject gen;
    gen.obj = obj;
    gen.has_state = has_state;
    generated_objs.push_back(std::move(gen));

    // Unpack state.
    if (has_state) {
      unpack_object_state(scan, obj);
    }
  }

  for (size_t i = 0; i < generated_objs.size(); ++i) {
    const GeneratedObject &gen = generated_objs[i];
    if (gen.has_state) {
      gen.obj->post_data_update();
    }
    gen.obj->generate();
  }
}

/**
 *
 */
void GameClient::
handle_delete_object(DatagramIterator &scan) {
  // Read objects to delete until end of stream.  Could be several at once.
  while (scan.get_remaining_size() > 0) {
    DO_ID doid = scan.get_uint32();
    ObjectMap::const_iterator it = _doid2do.find(doid);
    if (it != _doid2do.end()) {
      delete_object((*it).second);
    }
  }
}

/**
 * Handles a networked object RPC from the server.
 */
void GameClient::
handle_object_message(DatagramIterator &scan) {
  DO_ID doid = scan.get_uint32();
  uint16_t rpc_number = scan.get_uint16();

  ObjectMap::const_iterator it = _doid2do.find(doid);
  if (it == _doid2do.end()) {
    return;
  }

  NetworkObject *obj = (*it).second;
  NetworkClass *net_class = obj->get_network_class();

  NetworkRPC *rpc = net_class->get_inherited_rpc(rpc_number);
  if (rpc == nullptr) {
    return;
  }

  // Unpack message args and invoke the procedure.
  rpc->read(scan, obj);
}

/**
 *
 */
void GameClient::
disconnect() {
  if (!_connected) {
    return;
  }

  client_cat.info() << "Disconnecting from server\n";
  _server_address.clear();
  if (_connection != INVALID_STEAM_NETWORK_CONNECTION_HANDLE) {
    _net_sys->close_connection(_connection);
    _connection = INVALID_STEAM_NETWORK_CONNECTION_HANDLE;
  }
  _connected = false;
  _server_tick_rate = 0;
  _server_tick_interval = 0.0f;
  delete_all_objects();
}

/**
 *
 */
void GameClient::
handle_event(SteamNetworkEvent *event) {
  if (event->get_connection() != _connection) {
    // I don't think this is possible.. but just in case.
    return;
  }

  SteamNetworkEnums::NetworkConnectionState state = event->get_state();
  SteamNetworkEnums::NetworkConnectionState old_state = event->get_old_state();

  if (state == SteamNetworkEnums::NCS_connected) {
    // We've successfully connected.
    _connected = true;
    client_cat.info() << "Successfully connected to " << _server_address
                      << "\n";
    if (_connect_callback != nullptr) {
      (*_connect_callback)(this, true, _server_address);
    }

  } else if (old_state == SteamNetworkEnums::NCS_connecting) {
    // If old state was connecting and new state is not connected, we failed!
    client_cat.warning() << "Failed to connect to " << _server_address << "\n";
    _connected = false;
    _connection = INVALID_STEAM_NETWORK_CONNECTION_HANDLE;
    NetAddress server_addr = _server_address;
    _server_address.clear();
    if (_connect_callback != nullptr) {
      (*_connect_callback)(this, false, server_addr);
    }

  } else if (state == SteamNetworkEnums::NCS_closed_by_peer ||
             state == SteamNetworkEnums::NCS_problem_detected_locally) {
    // Lost connection
    _connected = false;
    client_cat.warning() << "Lost connection to server at " << _server_address
                         << "\n";
    if (_disconnect_callback != nullptr) {
      (*_disconnect_callback)(this);
    }
    _server_address.clear();
    _connection = INVALID_STEAM_NETWORK_CONNECTION_HANDLE;
    delete_all_objects();
  }
}

/**
 * Destroys the given networked object.
 */
void GameClient::
delete_object(NetworkObject *obj) {
  if (!obj->is_do_disabled()) {
    obj->disable();
    nassertv(obj->is_do_disabled());
  }

  // Remove from tables.  This should drop the final reference and
  // free the memory.
  ObjectMap::const_iterator it = _doid2do.find(obj->get_do_id());
  if (it != _doid2do.end()) {
    _doid2do.erase(it);
  }
}

/**
 * Destroys all networked objects that have been replicated to us.
 */
void
GameClient::delete_all_objects() {
  for (auto obj_entry : _doid2do) {
    NetworkObject *obj = obj_entry.second;
    if (!obj->is_do_disabled()) {
      obj->disable();
      nassertv(obj->is_do_disabled());
    }
  }
  _doid2do.clear();
}

/**
 * Interpolates all networked objects for the current rendering frame.
 */
void
GameClient::interpolate_objects() {
  //  float interp_time =
}

/**
 * Sends an RPC to the server on the given networked object.
 */
void GameClient::
send_obj_message(NetworkObject *obj, const std::string &name, void *msg_args) {
  NetworkClass *net_class = obj->get_network_class();
  int rpc_number = net_class->find_inherited_rpc(name);
  if (rpc_number == -1) {
    client_cat.warning()
      << "No RPC " << name << " on network class " << net_class->get_name() << "\n";
    return;
  }
  NetworkRPC *rpc = net_class->get_inherited_rpc(rpc_number);

  bool reliable = (rpc->flags & NetworkRPC::F_unreliable) == 0;

  Datagram dg;
  dg.add_uint16(NetMessages::B_object_message);
  dg.add_uint32(obj->get_do_id());
  dg.add_uint16(rpc_number);
  rpc->write(dg, msg_args);
  send_datagram(dg, reliable);
}

/**
 *
 */
void
GameClient::handle_server_world_update(DatagramIterator &scan) {
  int old_tick = _server_tick_count;
  _server_tick_count = scan.get_uint32();

  bool is_delta = scan.get_bool();

  if (is_delta && _delta_tick < 0) {
    // We requested a full update but got a delta compressed update.
    // Ignore it.
    _server_tick_count = old_tick;
    return;
  }

  _last_server_tick_time = _server_tick_count * _server_tick_interval;

  //TODO:
  //_clock_drift_mgr->set_server_tick(_server_tick_count);

  enter_simulation_time(_server_tick_count);

  _last_update_time = get_client_time();

  // TODO: PREDICTION STUFF

  unpack_server_snapshot(scan);

  // TODO: PREDICTION POST ENTITY PACKET RECEIVED

  // Restore the true client tick count and frame time.
  exit_simulation_time();

  if (_delta_tick >= 0 || !is_delta) {
    // We have a new delta reference.
    _delta_tick = _server_tick_count;
  }
}

/**
 *
 */
void GameClient::
send_tick() {
  Datagram dg;
  dg.add_uint16(NetMessages::CL_world_update_ack);
  dg.add_int32(_delta_tick);
  send_datagram(dg, false);
}

/**
 *
 */
bool GameClient::
unpack_object_state(DatagramIterator &scan, NetworkObject *obj) {
  NetworkClass *net_class = obj->get_network_class();
  DO_ID doid = obj->get_do_id();

  obj->pre_data_update();

  int num_fields = scan.get_uint16();

  if (client_cat.is_debug()) {
    client_cat.debug()
      << "Unpacking " << num_fields << " fields on object " << doid << "\n";
  }

  for (int i = 0; i < num_fields; ++i) {
    int field_number = scan.get_uint16();

    NetworkField *field = net_class->get_inherited_field(field_number);
    if (field == nullptr) {
      client_cat.error()
        << "Inherited field " << field_number << " not found on " << doid << "\n";
      return false;
    }

    if (client_cat.is_debug()) {
      client_cat.debug()
	<< "Receive data for field " << field->name << "\n";
    }

    size_t start_remaining = scan.get_remaining_size();
    field->read(obj, scan);
    size_t end_remaining = scan.get_remaining_size();
  }

  return true;
}

/**
 *
 */
void GameClient::
unpack_server_snapshot(DatagramIterator &scan) {
  int num_objects = scan.get_uint16();

  if (client_cat.is_debug()) {
    client_cat.debug()
      << num_objects << " objects in snapshot\n";
  }

  pvector<NetworkObject *> unpacked;
  unpacked.reserve(num_objects);

  for (int i = 0; i < num_objects; ++i) {
    DO_ID doid = scan.get_uint32();
    ObjectMap::const_iterator it = _doid2do.find(doid);
    if (it == _doid2do.end()) {
      client_cat.error()
        << "State snapshot has data for DO ID " << doid << ", but we don't have "
        << "that object in our table. Object index " << i << "\n";
      return;
    }

    NetworkObject *obj = (*it).second;

    if (!unpack_object_state(scan, obj)) {
      client_cat.error()
        << "Failed to unpack object state for DO " << doid << "\n";
      return;
    }

    unpacked.push_back(obj);
  }

  // After unpacking all data, call post_data_update() on all the objects
  // that had state updated.
  for (size_t i = 0; i < unpacked.size(); ++i) {
    NetworkObject *obj = unpacked[i];
    obj->post_data_update();
  }
}

/**
 * Sends a message to the server.
 */
void GameClient::
send_datagram(Datagram &dg, bool reliable) {
  if (dg.get_length() == 0u || !_connected) {
    return;
  }
  SteamNetworkEnums::NetworkSendFlags send_type;
  if (reliable) {
    send_type = SteamNetworkEnums::NSF_reliable_no_nagle;
  } else {
    send_type = SteamNetworkEnums::NSF_unreliable_no_delay;
  }
  _net_sys->send_datagram(_connection, dg, send_type);
}

/**
 *
 */
void GameClient::
send_hello(SignOnCallback callback, const std::string &password) {
  _sign_on_callback = callback;
  Datagram dg;
  dg.add_uint16(NetMessages::CL_hello);
  dg.add_string(password);
  // TODO: Verify network class protocol??
  dg.add_uint8(cl_update_rate);
  dg.add_uint8(cl_cmd_rate);
  dg.add_float32(get_client_interp_amount());
  send_datagram(dg);
}

/**
 *
 */
GameClient *GameClient::
ptr() {
  if (_ptr == nullptr) {
    _ptr = new GameClient;
  }
  return _ptr;
}

#endif // CLIENT

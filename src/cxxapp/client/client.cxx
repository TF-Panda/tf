#ifdef CLIENT

#include "client.h"
#include "pnotify.h"
#include "steamNetworkMessage.h"
#include "steamnet_includes.h"
#include "../netMessages.h"
#include "../networkClassRegistry.h"
#include "../networkClass.h"

NotifyCategoryDeclNoExport(client);
NotifyCategoryDef(client, "tf");

/**
 *
 */
void
Client::try_connect(const NetAddress &addr) {
  client_cat.info() << "Attempting to connect to " << addr << "\n";
  _server_address = addr;
  _connection = _net_sys->connect_by_IP_address(addr);
  if (_connection == INVALID_STEAM_NETWORK_CONNECTION_HANDLE) {
    client_cat.warning() << "Immediate failure connecting to " << addr << "\n";
    _server_address.clear();
  }
}

/**
 *
 */
void
Client::run_simulation() {
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
  PT(SteamNetworkEvent) ev = _net_sys->get_next_event();
  while (ev != nullptr) {
    handle_event(ev);
    ev = _net_sys->get_next_event();
  }
}

/**
 *
 */
void
Client::handle_message(SteamNetworkMessage *msg) {
  DatagramIterator &scan = msg->get_datagram_iterator();
  NetMessages::MessageType msg_type = (NetMessages::MessageType)scan.get_uint16();

  switch (msg_type) {
  case NetMessages::SV_hello_resp:
    handle_server_hello_resp(scan);
    break;
  case NetMessages::SV_generate_object:
    handle_generate_object(scan);
    break;
  case NetMessages::SV_world_update:
    handle_server_world_update(scan);
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
Client::handle_server_hello_resp(DatagramIterator &scan) {
  bool ret = scan.get_bool();

  if (ret) {
    client_cat.info() << "Signed onto server\n";
    _server_tick_rate = scan.get_uint8();
    _server_tick_interval = 1.0f / _server_tick_rate;

  } else {
    _disconnect_reason = scan.get_string();
    client_cat.warning() << "Failed to sign onto server: "  << _disconnect_reason << "\n";
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
void Client::
handle_generate_object(DatagramIterator &scan) {
  NetworkClassRegistry *reg = NetworkClassRegistry::ptr();

  pvector<GeneratedObject> generated_objs;

  // Generate message can contain multiple objects.
  while (scan.get_remaining_size() > 0) {
    uint16_t classid = scan.get_uint16();
    DO_ID doid = scan.get_uint32();
    ZONE_ID zoneid = scan.get_uint32();
    bool has_state = scan.get_bool();

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
void
Client::disconnect() {
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
  delete_all_objects();
}

/**
 *
 */
void
Client::handle_event(SteamNetworkEvent *event) {
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

  } else if (old_state == SteamNetworkEnums::NCS_connecting) {
    // If old state was connecting and new state is not connected, we failed!
    client_cat.warning() << "Failed to connect to " << _server_address << "\n";
    _connected = false;
    _connection = INVALID_STEAM_NETWORK_CONNECTION_HANDLE;
    _server_address.clear();

  } else if (state == SteamNetworkEnums::NCS_closed_by_peer ||
             state == SteamNetworkEnums::NCS_problem_detected_locally) {
    // Lost connection
    _connected = false;
    client_cat.warning() << "Lost connection to server at " << _server_address
                         << "\n";
    _server_address.clear();
    _connection = INVALID_STEAM_NETWORK_CONNECTION_HANDLE;
    delete_all_objects();
  }
}

/**
 *
 */
void
Client::delete_all_objects() {
  // TODO
}

/**
 * Interpolates all networked objects for the current rendering frame.
 */
void
Client::interpolate_objects() {
  //  float interp_time =
}

/**
 *
 */
void
Client::handle_server_world_update(DatagramIterator &scan) {
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
bool Client::
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

    field->read(obj, scan);
  }

  return true;
}

/**
 *
 */
void Client::
unpack_server_snapshot(DatagramIterator &scan) {
  int num_objects = scan.get_uint16();

  pvector<NetworkObject *> unpacked;
  unpacked.reserve(num_objects);

  for (int i = 0; i < num_objects; ++i) {
    DO_ID doid = scan.get_uint32();
    ObjectMap::const_iterator it = _doid2do.find(doid);
    if (it == _doid2do.end()) {
      client_cat.error()
        << "State snapshot has data for DO ID " << doid << ", but we don't have "
        << "that object in our table.\n";
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

#endif // CLIENT

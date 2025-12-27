#include "client.h"
#include "pnotify.h"
#include "steamNetworkMessage.h"
#include "steamnet_includes.h"
#include "../netMessages.h"

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
Client::run_frame() {
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
  
}

/**
 *
 */
void
Client::handle_server_world_update(DatagramIterator &scan) {
  
}

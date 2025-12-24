#include "server.h"

#ifdef SERVER

#include "pandabase.h"
#include "steamNetworkMessage.h"

Server *Server::_global_ptr = nullptr;

Server::
Server() :
  _net_sys(SteamNetworkSystem::get_global_ptr())
{
}

void Server::
startup(int port) {
  _listen_socket = _net_sys->create_listen_socket(port);
  _poll_group = _net_sys->create_poll_group();
}

void Server::
handle_message(SteamNetworkMessage *msg) {

}

void Server::
handle_net_callback(SteamNetworkEvent *event) {

}

void Server::
run_frame() {
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

#endif // SERVER

#ifndef SERVER_H
#define SERVER_H

#define SERVER

#ifdef SERVER

#include "pandabase.h"
#include "steamNetworkSystem.h"
#include "referenceCount.h"
#include "pmap.h"
#include "pointerTo.h"

class SteamNetworkMessage;
class SteamNetworkEvent;

class Server {
public:
  class ClientConnection : ReferenceCount {
    enum ClientState {
      CS_unverified,
      CS_authenticating,
      CS_verified,
    };

    uint32_t id;
    NetAddress address;
    SteamNetworkConnectionHandle connection;
    ClientState state;

    // Managing how often we send world state updates to this client.
    int update_rate;
    float update_interval;
    float next_update_time;

    // How often we receive client commands from them.
    int cmd_rate;
    float cmd_interval;

    float interp_amount;
  };

private:
  Server();

  void handle_message(SteamNetworkMessage *msg);
  void handle_net_callback(SteamNetworkEvent *event);

public:
  void startup(int port);
  void run_frame();

private:
  SteamNetworkSystem *_net_sys;
  SteamNetworkPollGroupHandle _poll_group;
  SteamNetworkListenSocketHandle _listen_socket;

  typedef pflat_hash_map<SteamNetworkConnectionHandle, PT(ClientConnection)> ClientConnections;
  ClientConnections _client_connections;

public:
  inline static Server *ptr();
private:
  static Server *_global_ptr;
};

inline Server *Server::
ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new Server;
  }
  return _global_ptr;
}

#endif // SERVER

#endif // SERVER_H

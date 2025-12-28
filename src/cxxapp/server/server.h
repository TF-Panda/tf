#ifndef SERVER_H
#define SERVER_H

#include "datagramIterator.h"

#ifdef SERVER

#include "pandabase.h"
#include "steamNetworkSystem.h"
#include "referenceCount.h"
#include "pmap.h"
#include "pointerTo.h"
#include "../networkObject.h"
#include "../simulationManager.h"
#include "pset.h"

class SteamNetworkMessage;
class SteamNetworkEvent;
class NetworkObject;

/**
 *
 */
class ClientConnection : public ReferenceCount {
public:
  enum ClientState {
    CS_unverified,
    CS_authenticating,
    CS_verified,
  };

  int32_t id;
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

  // A client can have objects owned by it that are automatically deleted
  // when the client disconnects.  Main example is their player object.
  typedef pflat_hash_map<DO_ID, NetworkObject *, integer_hash<DO_ID>> ObjectsByDoID;
  ObjectsByDoID objects_by_do_id;

  // Network zones the client has interest in/can see.  Any networked objects in
  // the client's set of interest zones will be replicated to them.
  typedef pset<ZONE_ID> InterestZones;
  InterestZones _interest_zones;
};

/**
 *
 */
class Server : public SimulationManager {
private:
  Server();

  void handle_message(SteamNetworkMessage *msg);
  void handle_net_callback(SteamNetworkEvent *event);
  void handle_connecting_client(SteamNetworkConnectionHandle conn);
  void handle_disconnecting_client(ClientConnection *client);
  void handle_client_hello(ClientConnection *client, DatagramIterator &scan);

  bool ensure_datagram_size(size_t size, DatagramIterator &scan, ClientConnection *client);

public:
  void startup(int port);
  virtual void run_simulation() override;

  void add_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones);
  void remove_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones);
  void update_client_interest(ClientConnection *client, const pset<ZONE_ID> &zones);

  void send_datagram(const Datagram &dg, SteamNetworkConnectionHandle conn, bool reliable = true);
  void close_client_connection(ClientConnection *client);

  bool can_accept_connection() const;

  void generate_object(NetworkObject *obj, ZONE_ID zone_id, ClientConnection *owner = nullptr);
  void delete_object(NetworkObject *obj);

  inline NetworkObject *get_do_by_id(DO_ID do_id) const;

private:
  SteamNetworkSystem *_net_sys;
  SteamNetworkPollGroupHandle _poll_group;
  SteamNetworkListenSocketHandle _listen_socket;

  int _num_clients;
  DO_ID _next_do_id;

  typedef pflat_hash_map<SteamNetworkConnectionHandle, PT(ClientConnection), integer_hash<SteamNetworkConnectionHandle>> ClientConnections;
  ClientConnections _client_connections;

  typedef pmap<DO_ID, PT(NetworkObject)> ObjectsByID;
  typedef pset<PT(NetworkObject)> ObjectSet;
  typedef pmap<DO_ID, ObjectSet> ObjectsByZoneID;
  ObjectsByID _doid2do;
  ObjectsByZoneID _zoneid2do;

  std::string _password;

public:
  inline static Server *ptr();
private:
  static Server *_global_ptr;
};

/**
 *
 */
inline NetworkObject *Server::
get_do_by_id(DO_ID do_id) const {
  ObjectsByID::const_iterator it = _doid2do.find(do_id);
  if (it == _doid2do.end()) {
    return nullptr;
  }
  return (*it).second;
}


/**
 *
 */
inline Server *Server::
ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new Server;
  }
  return _global_ptr;
}

#endif // SERVER

#endif // SERVER_H

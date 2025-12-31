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
#include "networkSnapshotManager.h"

class SteamNetworkMessage;
class SteamNetworkEvent;
class NetworkObject;

constexpr ZONE_ID game_manager_zone = 1u;
constexpr ZONE_ID game_zone = 2u;

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

  int32_t id = -1;
  NetAddress address;
  SteamNetworkConnectionHandle connection = INVALID_STEAM_NETWORK_CONNECTION_HANDLE;
  ClientState state = CS_unverified;

  // Managing how often we send world state updates to this client.
  int update_rate = 0;
  float update_interval = 0.0f;
  float next_update_time = 0.0f;

  // Last acknowledged snapshot tick.
  int delta_tick = -1;

  // How often we receive client commands from them.
  int cmd_rate = 0;
  float cmd_interval = 0.0f;

  float interp_amount = 0.0f;

  // Ring buffer of most recently sent snapshots to this client.
  ClientFrameList frame_list;

  // A client can have objects owned by it that are automatically deleted
  // when the client disconnects.  Main example is their player object.
  typedef pflat_hash_map<DO_ID, NetworkObject *, integer_hash<DO_ID>> ObjectsByDoID;
  ObjectsByDoID objects_by_do_id;

  // Network zones the client has interest in/can see.  Any networked objects in
  // the client's set of interest zones will be replicated to them.
  typedef pset<ZONE_ID> InterestZones;
  InterestZones interest_zones;

  inline bool has_interest(ZONE_ID zone) const;
  inline const ClientFrame *get_client_frame(int tick) const;
};

/**
 *
 */
class GameServer : public SimulationManager {
private:
  GameServer();

  void handle_message(SteamNetworkMessage *msg);
  void handle_net_callback(SteamNetworkEvent *event);
  void handle_connecting_client(SteamNetworkConnectionHandle conn);
  void handle_disconnecting_client(ClientConnection *client);
  void handle_client_hello(ClientConnection *client, DatagramIterator &scan);
  void handle_object_message(ClientConnection *client, DatagramIterator &scan);
  void handle_client_tick(ClientConnection *client, DatagramIterator &scan);

  bool ensure_datagram_size(size_t size, DatagramIterator &scan, ClientConnection *client);

  void pack_object_generate(Datagram &dg, NetworkObject *obj, bool owner);

public:
  void startup(int port);
  virtual void run_simulation() override;
  virtual void post_simulate() override;

  void add_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones);
  void remove_client_interest(ClientConnection *client, const pvector<ZONE_ID> &zones);
  void update_client_interest(ClientConnection *client, const pset<ZONE_ID> &zones);

  void send_obj_message(NetworkObject *obj, const std::string &msg_name, void *msg_args,
			ClientConnection *client = nullptr,
			const pvector<ClientConnection *> &exclude_clients = pvector<ClientConnection *>());

  void send_datagram(const Datagram &dg, SteamNetworkConnectionHandle conn, bool reliable = true);
  void close_client_connection(ClientConnection *client);

  bool can_accept_connection() const;

  void generate_object(NetworkObject *obj, ZONE_ID zone_id, ClientConnection *owner = nullptr);
  void delete_object(NetworkObject *obj);

  void take_tick_snapshot(int tick_count);

  inline NetworkObject *get_do_by_id(DO_ID do_id) const;

  inline ClientConnection *get_client_sender() const;

  inline int get_max_clients() const;

private:
  SteamNetworkSystem *_net_sys;
  SteamNetworkPollGroupHandle _poll_group;
  SteamNetworkListenSocketHandle _listen_socket;

  int _num_clients;
  DO_ID _next_do_id;
  int _next_client_id;
  int _max_clients;

  typedef pflat_hash_map<SteamNetworkConnectionHandle, PT(ClientConnection), integer_hash<SteamNetworkConnectionHandle>> ClientConnections;
  ClientConnections _client_connections;

  typedef pmap<DO_ID, PT(NetworkObject)> ObjectsByID;
  typedef pset<PT(NetworkObject)> ObjectSet;
  typedef pmap<DO_ID, ObjectSet> ObjectsByZoneID;
  ObjectsByID _doid2do;
  ObjectsByZoneID _zoneid2do;

  std::string _password;

  NetworkSnapshotManager _snapshot_mgr;

  // Client that sent the current RPC we are processing.
  // This will only be set when invoking a received RPC.
  ClientConnection *_client_sender;

public:
  inline static GameServer *ptr();
private:
  static GameServer *_global_ptr;
};

/**
 *
 */
inline NetworkObject *GameServer::
get_do_by_id(DO_ID do_id) const {
  ObjectsByID::const_iterator it = _doid2do.find(do_id);
  if (it == _doid2do.end()) {
    return nullptr;
  }
  return (*it).second;
}

/**
 * Returns the client that sent the RPC that is currently being invoked.  Will
 * be nullptr if we're not currently in an RPC invocation.
 */
inline ClientConnection *GameServer::
get_client_sender() const {
  return _client_sender;
}

/**
 *
 */
inline int GameServer::
get_max_clients() const {
  return _max_clients;
}

/**
 *
 */
inline GameServer *GameServer::
ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new GameServer;
  }
  return _global_ptr;
}

/**
 *
 */
inline bool ClientConnection::
has_interest(ZONE_ID zone) const {
  return interest_zones.find(zone) != interest_zones.end();
}

/**
 *
 */
inline const ClientFrame *ClientConnection::
get_client_frame(int tick) const {
  return frame_list.get_client_frame(tick);
}

#endif // SERVER

#endif // SERVER_H

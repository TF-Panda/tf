#ifndef CLIENT_H
#define CLIENT_H

#include "../networkObject.h"
#include "netAddress.h"
#include "pmap.h"
#include "pointerTo.h"
#include "steamNetworkSystem.h"
#include "steamnet_includes.h"
#include "../simulationManager.h"

/**
 * Manages the client's connection to the server.  Also manages networked
 * objects replicated by the server.
 */
class GameClient : public SimulationManager {
public:
  typedef void (*ConnectCallback)(GameClient *client, bool success, const NetAddress &addr);
  typedef void (*SignOnCallback)(GameClient *client, bool success, const std::string &msg);
  typedef void (*DisconnectCallback)(GameClient *client);

  inline GameClient();

  inline void set_disconnect_callback(DisconnectCallback callback);

  void try_connect(const NetAddress &addr, ConnectCallback callback);
  virtual void run_simulation() override;

  void interpolate_objects();

  void send_obj_message(NetworkObject *obj, const std::string &msg_name, void *msg_args);

  inline NetworkObject *get_do(DO_ID id) const;

  inline const std::string &get_disconnect_reason() const;

  inline int get_server_tick_rate() const;
  inline float get_server_tick_interval() const;
  inline float get_last_server_tick_time() const;

  inline bool is_connected() const;

  void disconnect();

  void delete_object(NetworkObject *obj);
  void delete_all_objects();

  void send_datagram(Datagram &dg, bool reliable = true);

  void send_hello(SignOnCallback callback, const std::string &password = "");

  void send_tick();

private:
  void handle_message(SteamNetworkMessage *msg);
  void handle_event(SteamNetworkEvent *event);

  void handle_server_hello_resp(DatagramIterator &scan);
  void handle_server_world_update(DatagramIterator &scan);
  void handle_generate_object(DatagramIterator &scan);
  void handle_delete_object(DatagramIterator &scan);
  void handle_object_message(DatagramIterator &scan);

  bool unpack_object_state(DatagramIterator &scan, NetworkObject *obj);
  void unpack_server_snapshot(DatagramIterator &scan);

private:
  ConnectCallback _connect_callback;
  SignOnCallback _sign_on_callback;
  DisconnectCallback _disconnect_callback;

  bool _connected;
  SteamNetworkConnectionHandle _connection;
  NetAddress _server_address;

  std::string _disconnect_reason;

  int _server_tick_rate;
  float _server_tick_interval;
  int _server_tick_count;
  float _last_server_tick_time;
  int _delta_tick;
  float _last_update_time;

  int _client_id;

  typedef pflat_hash_map<DO_ID, PT(NetworkObject), integer_hash<DO_ID>> ObjectMap;
  ObjectMap _doid2do;

  SteamNetworkSystem *_net_sys;

public:
  static GameClient *ptr();
private:
  static GameClient *_ptr;
};

/**
 *
 */
inline GameClient::GameClient() :
  _connected(false),
  _net_sys(SteamNetworkSystem::get_global_ptr()),
  _server_tick_rate(0),
  _server_tick_interval(0.0f),
  _connection(INVALID_STEAM_NETWORK_CONNECTION_HANDLE),
  _server_tick_count(0),
  _last_server_tick_time(0.0f),
  _delta_tick(-1),
  _last_update_time(0.0f),
  _connect_callback(nullptr),
  _sign_on_callback(nullptr),
  _disconnect_callback(nullptr),
  _client_id(-1)
{
}

/**
 *
 */
inline void GameClient::
set_disconnect_callback(DisconnectCallback callback) {
  _disconnect_callback = callback;
}

/**
 * Returns the networked object with the given ID, or nullptr if no object
 * exists with the given ID.
 */
inline NetworkObject *
GameClient::get_do(DO_ID id) const {
  ObjectMap::const_iterator it = _doid2do.find(id);
  if (it == _doid2do.end()) {
    return nullptr;
  }
  return (*it).second;
}

/**
 *
 */
inline const std::string &
GameClient::get_disconnect_reason() const {
  return _disconnect_reason;
}

/**
 *
 */
inline int
GameClient::get_server_tick_rate() const {
  return _server_tick_rate;
}

/**
 *
 */
inline float
GameClient::get_server_tick_interval() const {
  return _server_tick_interval;
}

/**
 * Returns the network time of the most recently received server snapshot.
 */
inline float GameClient::
get_last_server_tick_time() const {
  return _last_server_tick_time;
}

/**
 *
 */
inline bool GameClient::
is_connected() const {
  return _connected;
}

#endif  // CLIENT_H

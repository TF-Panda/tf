#ifndef CLIENT_H
#define CLIENT_H

#include "../networkObject.h"
#include "netAddress.h"
#include "pandabase.h"
#include "pmap.h"
#include "pointerTo.h"
#include "steamNetworkSystem.h"
#include "steamnet_includes.h"
#include "../simulationManager.h"

/**
 * Manages the client's connection to the server.  Also manages networked
 * objects replicated by the server.
 */
class Client : public SimulationManager {
public:
  inline Client();

  void try_connect(const NetAddress &addr);
  virtual void run_simulation() override;

  void interpolate_objects();

  inline NetworkObject *get_do(DO_ID id) const;

  inline const std::string &get_disconnect_reason() const;

  inline int get_server_tick_rate() const;
  inline float get_server_tick_interval() const;

  void disconnect();

  void delete_all_objects();

private:
  void handle_message(SteamNetworkMessage *msg);
  void handle_event(SteamNetworkEvent *event);

  void handle_server_hello_resp(DatagramIterator &scan);
  void handle_server_world_update(DatagramIterator &scan);
  void handle_generate_object(DatagramIterator &scan);

  bool unpack_object_state(DatagramIterator &scan, NetworkObject *obj);
  void unpack_server_snapshot(DatagramIterator &scan);

private:
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

  typedef pflat_hash_map<DO_ID, PT(NetworkObject), integer_hash<DO_ID>> ObjectMap;
  ObjectMap _doid2do;

  SteamNetworkSystem *_net_sys;
};

/**
 *
 */
inline Client::Client() :
  _connected(false),
  _net_sys(SteamNetworkSystem::get_global_ptr()),
  _server_tick_rate(0),
  _server_tick_interval(0.0f),
  _connection(INVALID_STEAM_NETWORK_CONNECTION_HANDLE),
  _server_tick_count(0),
  _last_server_tick_time(0.0f),
  _delta_tick(-1),
  _last_update_time(0.0f)
{
}

/**
 * Returns the networked object with the given ID, or nullptr if no object
 * exists with the given ID.
 */
inline NetworkObject *
Client::get_do(DO_ID id) const {
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
Client::get_disconnect_reason() const {
  return _disconnect_reason;
}

/**
 *
 */
inline int
Client::get_server_tick_rate() const {
  return _server_tick_rate;
}

/**
 *
 */
inline float
Client::get_server_tick_interval() const {
  return _server_tick_interval;
}

#endif  // CLIENT_H

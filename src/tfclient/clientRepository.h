/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientRepository.h
 * @author brian
 * @date 2022-05-05
 */

#ifndef CLIENTREPOSITORY_H
#define CLIENTREPOSITORY_H

#include "tfbase.h"
#include "networkRepository.h"
#include "steamNetworkSystem.h"
#include "netAddress.h"
#include "netMessages.h"
#include "genericAsyncTask.h"
#include "notifyCategoryProxy.h"

NotifyCategoryDeclNoExport(clientrepository);

class DistributedObject;

/**
 *
 */
class ClientRepository : public NetworkRepository {
  DECLARE_CLASS(ClientRepository, NetworkRepository);

public:
  ClientRepository();

  void start_client_loop();
  void stop_client_loop();

  bool connect(const NetAddress &address);

  void send_hello(const std::string &password);
  void handle_server_hello_resp(DatagramIterator &scan);

  bool reader_poll_once();
  INLINE void reader_poll_until_empty();

  void run_callbacks();
  void handle_net_callback(SteamNetworkConnectionHandle conn,
                           SteamNetworkEnums::NetworkConnectionState state,
                           SteamNetworkEnums::NetworkConnectionState old_state);

  void handle_datagram(DatagramIterator &scan, NetMessage msg_type);

  void handle_generate_object(DatagramIterator &scan);
  bool unpack_object_state(DistributedObject *obj, DatagramIterator &scan);
  void handle_delete_object(DatagramIterator &scan);
  void handle_server_tick(DatagramIterator &scan);
  bool unpack_server_snapshot(DatagramIterator &scan, bool is_delta);

  void delete_object(NetworkedObjectBase *obj);
  void delete_all_objects();

  void send_datagram(const Datagram &dg, bool reliable = true);

  INLINE bool is_connected() const;
  INLINE const NetAddress &get_server_address() const;

  static AsyncTask::DoneStatus reader_poll_task(GenericAsyncTask *task, void *data);
  static AsyncTask::DoneStatus callbacks_task(GenericAsyncTask *task, void *data);
  static AsyncTask::DoneStatus interp_task(GenericAsyncTask *task, void *data);

protected:
  SteamNetworkSystem *_net_sys;
  SteamNetworkConnectionHandle _connection;
  bool _connected;
  NetAddress _server_address;

  PT(GenericAsyncTask) _reader_poll_task;
  PT(GenericAsyncTask) _callbacks_task;
  PT(GenericAsyncTask) _interp_task;

  double _server_interval_per_tick;
  int _delta_tick;
  int _server_tick_count;
  int _client_id;
};

#include "clientRepository.I"

#endif // CLIENTREPOSITORY_H

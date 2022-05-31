/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file serverRepository.h
 * @author brian
 * @date 2022-05-05
 */

#ifndef SERVERREPOSITORY_H
#define SERVERREPOSITORY_H

#include "pandabase.h"
#include "networkRepository.h"
#include "steamNetworkSystem.h"
#include "pmap.h"
#include "clientInfo.h"
#include "pointerTo.h"
#include "frameSnapshotManager.h"
#include "genericAsyncTask.h"

class SteamNetworkMessage;
class DistributedObjectAI;

/**
 *
 */
class ServerRepository : public NetworkRepository {
  DECLARE_CLASS(ServerRepository, NetworkRepository);

public:
  ServerRepository();

  void open_server(int port);

  void reader_poll_until_empty();
  bool reader_poll_once();

  void run_net_callbacks();
  void handle_datagram(SteamNetworkMessage *msg);
  void handle_net_callback(SteamNetworkConnectionHandle conn,
                           SteamNetworkEnums::NetworkConnectionState state,
                           SteamNetworkEnums::NetworkConnectionState old_state);

  void consider_send_snapshot(int tick);

  void handle_new_connection(SteamNetworkConnectionHandle conn,
                             const SteamNetworkConnectionInfo &info);
  void handle_client_hello(DatagramIterator &scan, ClientInfo *client);
  void handle_client_object_message(DatagramIterator &scan, ClientInfo *client);
  void handle_client_tick(DatagramIterator &scan, ClientInfo *client);
  void handle_client_level_loaded(DatagramIterator &scan, ClientInfo *client);

  void pack_object_generate(Datagram &dg, DistributedObjectAI *obj);
  void send_object_generates(ClientInfo *client);

  void send_datagram(const Datagram &dg, SteamNetworkConnectionHandle conn, bool reliable = true);

  bool ensure_datagram_size(size_t size, const DatagramIterator &scan, ClientInfo *client);

  void close_client_connection(ClientInfo *client);

  void generate_object(DistributedObjectAI *obj, zoneid_t zone_id, ClientInfo *owner = nullptr);

  static AsyncTask::DoneStatus reader_poll_task(GenericAsyncTask *task, void *data);
  static AsyncTask::DoneStatus callbacks_task(GenericAsyncTask *task, void *data);
  static AsyncTask::DoneStatus snapshot_task(GenericAsyncTask *task, void *data);

private:
  SteamNetworkSystem *_net_sys;
  SteamNetworkPollGroupHandle _poll_group;
  SteamNetworkListenSocketHandle _listen_socket;

  typedef pmap<SteamNetworkConnectionHandle, PT(ClientInfo)> ClientsByConnection;
  ClientsByConnection _clients_by_connection;

  FrameSnapshotManager _snapshot_mgr;

  PT(GenericAsyncTask) _reader_poll_task;
  PT(GenericAsyncTask) _callbacks_task;
  PT(GenericAsyncTask) _snapshot_task;

  uint32_t _next_client_id;
  uint32_t _next_do_id;
};

#include "serverRepository.I"

#endif // SERVERREPOSITORY_H

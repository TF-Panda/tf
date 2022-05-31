/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file serverRepository.cxx
 * @author brian
 * @date 2022-05-05
 */

#include "serverRepository.h"
#include "steamNetworkMessage.h"
#include "steamNetworkConnectionInfo.h"
#include "networkedObjectRegistry.h"
#include "../shared/netMessages.h"
#include "networkClass.h"
#include "distributedObjectAI.h"
#include "frameSnapshot.h"
#include "clockObject.h"
#include "asyncTaskManager.h"
#include "simulationManager.h"
#include "config_tfai.h"
#include "configVariableInt.h"
#include "tfAIBase.h"

extern ConfigVariableDouble server_tick_rate;

IMPLEMENT_CLASS(ServerRepository);

/**
 *
 */
ServerRepository::
ServerRepository() :
  _net_sys(SteamNetworkSystem::get_global_ptr()),
  _poll_group(INVALID_STEAM_NETWORK_POLL_GROUP_HANDLE),
  _listen_socket(INVALID_STEAM_NETWORK_LISTEN_SOCKET_HANDLE),
  _next_client_id(0u),
  _next_do_id(0u)
{
}

/**
 * Opens a listener socket on the indicated port.
 */
void ServerRepository::
open_server(int port) {
  tfai_cat.info()
    << "Opening server on port " << port << "\n";

  _poll_group = _net_sys->create_poll_group();
  _listen_socket = _net_sys->create_listen_socket(port);

  _reader_poll_task = new GenericAsyncTask("readerPollTask", reader_poll_task, this);
  _reader_poll_task->set_sort(-100);
  _callbacks_task = new GenericAsyncTask("runNetCallbacks", callbacks_task, this);
  _callbacks_task->set_sort(-99);
  _snapshot_task = new GenericAsyncTask("takeTickSnapshot", snapshot_task, this);
  _snapshot_task->set_sort(1000);

  AsyncTaskManager *task_mgr = simbase->get_sim_task_mgr();
  task_mgr->add(_reader_poll_task);
  task_mgr->add(_callbacks_task);
  task_mgr->add(_snapshot_task);

  tfai_cat.info()
    << "Server opened\n";
}

/**
 * Reads and processes all queued messages received from connected clients.
 */
void ServerRepository::
reader_poll_until_empty() {
  while (reader_poll_once()) {
  }
}

/**
 * Attempts to read a single message off of the server's poll group and
 * process it.  Returns true if a message was received, or false otherwise.
 */
bool ServerRepository::
reader_poll_once() {
  SteamNetworkMessage msg;
  if (_net_sys->receive_message_on_poll_group(_poll_group, msg)) {
    handle_datagram(&msg);
    return true;
  }
  return false;
}

/**
 *
 */
void ServerRepository::
run_net_callbacks() {
  _net_sys->run_callbacks();
  PT(SteamNetworkEvent) event = _net_sys->get_next_event();
  while (event != nullptr) {
    handle_net_callback(event->get_connection(), event->get_state(), event->get_old_state());
    event = _net_sys->get_next_event();
  }
}

/**
 * Reads and processes a message received from a client.
 */
void ServerRepository::
handle_datagram(SteamNetworkMessage *msg) {
  DatagramIterator &scan = msg->get_datagram_iterator();
  SteamNetworkConnectionHandle conn = msg->get_connection();
  // Find the client using the connection handle that sent the message.
  ClientsByConnection::const_iterator it = _clients_by_connection.find(conn);
  if (it == _clients_by_connection.end()) {
    tfai_cat.warning()
      << "Received message from unrecognized connection " << conn << "\n";
    // Got message from unrecorded client.  Not sure how this would be
    // possible, but it's a good idea to handle this.
    _net_sys->close_connection(conn);
    return;
  }
  ClientInfo *client = (*it).second;

  if (!ensure_datagram_size(1u, scan, client)) {
    return;
  }
  NetMessage msg_type = (NetMessage)scan.get_uint8();

  if (tfai_cat.is_debug()) {
    tfai_cat.debug()
      << "Received message " << msg_type << " from client " << client->_id
      << " in state " << client->_state << "\n";
  }

  switch (client->_state) {
  case ClientInfo::CS_unverified:
    switch (msg_type) {
    case NM_cl_hello:
      handle_client_hello(scan, client);
      break;
    default:
      close_client_connection(client);
      break;
    }
    break;
  case ClientInfo::CS_loading_level:
    switch (msg_type) {
    case NM_cl_level_loaded:
      handle_client_level_loaded(scan, client);
      break;
    default:
      close_client_connection(client);
      break;
    }
    break;
  case ClientInfo::CS_playing:
    switch (msg_type) {
    case NM_b_object_message:
      handle_client_object_message(scan, client);
      break;
    case NM_cl_tick:
      handle_client_tick(scan, client);
      break;
    default:
      close_client_connection(client);
      break;
    }
    break;
  }
}

/**
 * Handles a "tick" message from a client, which acknowledges a previously
 * sent snapshot from the server.
 */
void ServerRepository::
handle_client_tick(DatagramIterator &scan, ClientInfo *client) {
  if (!ensure_datagram_size(4u, scan, client)) {
    return;
  }
  client->_delta_tick = scan.get_int32();
}

/**
 *
 */
void ServerRepository::
handle_client_object_message(DatagramIterator &scan, ClientInfo *client) {
  // 4 byte object ID and 2 byte message index.
  if (!ensure_datagram_size(6u, scan, client)) {
    return;
  }
  doid_t do_id = scan.get_uint32();
  DistributedObjectAI *obj = (DistributedObjectAI *)get_object(do_id);
  if (obj == nullptr) {
    close_client_connection(client);
    return;
  }

  NetworkClass *dclass = obj->get_network_class();
  uint16_t msg_index = scan.get_uint16();
  const NetworkClass::MessageDef *msg = dclass->get_message(msg_index);
  if (msg == nullptr) {
    close_client_connection(client);
    return;
  }

  bool can_receive = true;

  if (obj->get_owner() != client) {
    // Client doesn't own this object.  It can only send messages
    // marked as clsend.
    if ((msg->_flags & NetworkClass::MF_clsend) == 0) {
      can_receive = false;
    }
  } else {
    // Client owns the object, therefore has the priviledge of sending
    // messages marked as ownsend or clsend.
    if ((msg->_flags & (NetworkClass::MF_ownsend | NetworkClass::MF_clsend)) == 0) {
      can_receive = false;
    }
  }

  if (!can_receive) {
    close_client_connection(client);
    return;
  }

  // We can allow the message handler to process the message.
  (*msg->_func)(scan, obj);
}

/**
 *
 */
void ServerRepository::
handle_client_hello(DatagramIterator &scan, ClientInfo *client) {
  if (!ensure_datagram_size(2u, scan, client)) {
    return;
  }
  std::string password = scan.get_string();

  if (!ensure_datagram_size(2u, scan, client)) {
    return;
  }
  client->_name = scan.get_string();

  if (!ensure_datagram_size(2u, scan, client)) {
    return;
  }
  uint8_t update_rate = scan.get_uint8();
  uint8_t cmd_rate = scan.get_uint8();
  client->_update_rate = update_rate;
  client->_update_interval = 1.0f / (float)update_rate;
  client->_cmd_rate = cmd_rate;
  client->_cmd_interval = 1.0f / (float)cmd_rate;

  tfai_cat.info()
    << "Got hello from connection " << client->_connection << ", ID " << client->_id << "\n";
  tfai_cat.info()
    << "Client update rate: " << client->_update_rate << ", cmd rate: " << client->_cmd_rate << "\n";
  tfai_cat.info()
    << "Player name: " << client->_name << "\n";

  // Prepare our response.
  Datagram dg;
  dg.add_uint8(NM_sv_hello_resp);
  dg.add_uint32(client->_id);
  dg.add_uint8(client->_update_rate);
  dg.add_uint8(client->_cmd_rate);
  dg.add_uint8(server_tick_rate);

#if 0
  // Send our entire network class registry so the client can synchronize
  // their IDs.
  NetworkedObjectRegistry *net_reg = NetworkedObjectRegistry::get_global_ptr();
  dg.add_uint16(net_reg->get_num_classes());
  for (size_t i = 0; i < net_reg->get_num_classes(); ++i) {
    NetworkClass *cls = net_reg->get_class(i);
    dg.add_string(cls->get_name());
    dg.add_uint16(cls->get_num_fields());
    for (size_t j = 0; j < cls->get_num_fields(); ++j) {
      NetworkField *field = cls->get_field(j);
      dg.add_string(field->get_name());
    }
  }
#endif

  // TODO: Add current level name.

  client->_state = ClientInfo::CS_loading_level;

  send_datagram(dg, client->_connection);
}

/**
 *
 */
bool ServerRepository::
ensure_datagram_size(size_t size, const DatagramIterator &scan, ClientInfo *client) {
  if (scan.get_remaining_size() < size) {
    tfai_cat.warning()
      << "Client connection " << client->_connection << " (ID " << client->_id << ") "
      << "sent truncated message in state " << client->_state << ".  Expected " << size
      << " bytes in datagram, but only " << scan.get_remaining_size() << " bytes remain. "
      << "Closing connection.\n";
    close_client_connection(client);
    return false;
  }
  return true;
}

/**
 *
 */
void ServerRepository::
close_client_connection(ClientInfo *client) {
  tfai_cat.info()
    << "Closing client connection " << client->_connection << " (ID " << client->_id << ")\n";
  _net_sys->close_connection(client->_connection);
  ClientsByConnection::const_iterator it = _clients_by_connection.find(client->_connection);
  if (it != _clients_by_connection.end()) {
    _clients_by_connection.erase(it);
  }
}

/**
 *
 */
void ServerRepository::
handle_net_callback(SteamNetworkConnectionHandle conn,
                    SteamNetworkEnums::NetworkConnectionState state,
                    SteamNetworkEnums::NetworkConnectionState old_state) {
  if (state == SteamNetworkEnums::NCS_connecting) {
    //if (!can_accept_connection()) {
    //  return;
    //}
    if (!_net_sys->accept_connection(conn)) {
      tfai_cat.warning()
        << "Couldn't accept new connection " << conn << "\n";
      return;
    }
    if (!_net_sys->set_connection_poll_group(conn, _poll_group)) {
      tfai_cat.warning()
        << "Couldn't set poll group for new connection " << conn << "\n";
      _net_sys->close_connection(conn);
      return;
    }
    SteamNetworkConnectionInfo info;
    _net_sys->get_connection_info(conn, &info);
    handle_new_connection(conn, info);

  } else if (state == SteamNetworkEnums::NCS_closed_by_peer ||
             state == SteamNetworkEnums::NCS_problem_detected_locally) {
    auto it = _clients_by_connection.find(conn);
    if (it == _clients_by_connection.end()) {
      return;
    }
    ClientInfo *client = (*it).second;
    tfai_cat.info()
      << "Client " << client->_id << " (connection " << client->_connection << ") disconnected\n";
    close_client_connection(client);
  }
}

/**
 * Records a newly connected client.
 */
void ServerRepository::
handle_new_connection(SteamNetworkConnectionHandle conn,
                      const SteamNetworkConnectionInfo &info) {
  if (_clients_by_connection.find(conn) != _clients_by_connection.end()) {
    tfai_cat.warning()
      << "Received redundant new connection for connection " << conn << "\n";
    return;
  }

  PT(ClientInfo) client = new ClientInfo;
  client->_connection = conn;
  client->_net_address = info.get_net_address();
  client->_id = _next_client_id++;
  _clients_by_connection.insert({ conn, client });

  tfai_cat.info()
    << "Got new connection " << conn << " from " << client->_net_address
    << ", given ID " << client->_id << ", awaiting hello.\n";
}

/**
 *
 */
void ServerRepository::
consider_send_snapshot(int tick) {
  ClockObject *clock = ClockObject::get_global_clock();
  PN_stdfloat now = (PN_stdfloat)clock->get_frame_time();

  PT(FrameSnapshot) snap = new FrameSnapshot(tick, (int)_net_obj_table.size());

  // Determine which clients need a state update.
  zoneset_t all_client_zones;
  pvector<ClientInfo *> clients_needing_snapshots;
  for (auto it = _clients_by_connection.begin(); it != _clients_by_connection.end(); ++it) {
    ClientInfo *client = (*it).second;
    if (client->needs_update(now)) {
      all_client_zones.insert(client->_interest.begin(), client->_interest.end());
      clients_needing_snapshots.push_back(client);
      client->_next_update_time = now + client->_update_interval;
      client->setup_pack_info(snap);
    }
  }

  if (clients_needing_snapshots.empty()) {
    // No clients need a state update right now, so there's no need to build
    // a state snapshot.
    return;
  }

  // Pack all objects visible by at least one client into the snapshot.
  int i = 0;
  for (auto it = _net_obj_table.begin(); it != _net_obj_table.end(); ++it, ++i) {
    NetworkedObjectBase *obj = (*it).second;
    //if (all_client_zones.find(obj->get_zone_id()) == all_client_zones.end()) {
    //  // Object not seen by any clients, omit from snapshot.
    //  continue;
    //}
    // Pack the object's state into the snapshot and calculate the delta from
    // the previous snapshot.
    _snapshot_mgr.pack_object_in_snapshot(snap, i, obj);
  }

  // Send it out to whoever needs it.
  for (ClientInfo *client : clients_needing_snapshots) {
    ClientFrame *old_frame = client->_frame_mgr.get_client_frame(client->_delta_tick);

    Datagram dg;
    dg.add_uint8(NM_sv_tick);
    if (old_frame != nullptr) {
      // We have a previously acknowledged state to delta the packet against.
      _snapshot_mgr.client_format_delta_snapshot(dg, old_frame->get_snapshot(), snap, client->_interest);
    } else {
      // No delta reference, send absolute state.
      _snapshot_mgr.client_format_snapshot(dg, snap, client->_interest);
    }
    send_datagram(dg, client->_connection, false);
  }
}

/**
 *
 */
void ServerRepository::
send_datagram(const Datagram &dg, SteamNetworkConnectionHandle conn, bool reliable) {
  _net_sys->send_datagram(conn, dg, reliable ? SteamNetworkEnums::NSF_reliable_no_nagle : SteamNetworkEnums::NSF_unreliable_no_delay);
}

/**
 * Packs a generate message into the datagram for the indicated object.
 * Writes the NetworkClass ID, NetworkedObject ID, and absolute state of
 * the object into the datagram.
 */
void ServerRepository::
pack_object_generate(Datagram &dg, DistributedObjectAI *obj) {
  NetworkClass *dclass = obj->get_network_class();
  dg.add_uint16(dclass->get_id());
  dg.add_uint32(obj->get_network_id());
  dg.add_uint32(obj->get_zone_id());
  PackedObject *baseline = _snapshot_mgr.
    find_or_create_object_packet_for_baseline(obj);
  if (baseline != nullptr) {
    dg.add_uint8(1);
    baseline->pack_datagram(dg);
  } else {
    dg.add_uint8(0);
  }
}

/**
 * Sends a generate packet to the indicated client that instructs the client
 * to instantiate all objects in the world and apply an initial state to them.
 */
void ServerRepository::
send_object_generates(ClientInfo *client) {
  Datagram dg;
  dg.add_uint8(NM_sv_generate_object);
  for (auto it = _net_obj_table.begin(); it != _net_obj_table.end(); ++it) {
    NetworkedObjectBase *obj = (*it).second;
    nassertv(obj->is_of_type(DistributedObjectAI::get_class_type()));
    pack_object_generate(dg, DCAST(DistributedObjectAI, obj));
  }
  // Send it out.
  send_datagram(dg, client->_connection);
}

/**
 * Client is informing us that they finished loading the level.  We can now
 * send generates for all of the objects in the level.
 */
void ServerRepository::
handle_client_level_loaded(DatagramIterator &scan, ClientInfo *client) {
  tfai_cat.info()
    << "Client " << client->_id << " finished loading level, sending object "
    << "generates\n";
  client->_state = ClientInfo::CS_playing;
  send_object_generates(client);
}

/**
 *
 */
void ServerRepository::
generate_object(DistributedObjectAI *obj, zoneid_t zone, ClientInfo *owner) {
  assert(obj->is_do_fresh());

  obj->set_do_id(_next_do_id++);
  obj->set_zone_id(zone);
  obj->set_owner(owner);

  _net_obj_table.insert({ obj->get_do_id(), obj });

  obj->generate();
  assert(obj->is_do_generated());

  // Send out a generate message for this object to all clients
  // that can see it.
  Datagram dg;
  dg.add_uint8(NM_sv_generate_object);
  pack_object_generate(dg, obj);
  for (auto it = _clients_by_connection.begin(); it != _clients_by_connection.end(); ++it) {
    ClientInfo *client = (*it).second;
    if (client->_interest.find(zone) != client->_interest.end()) {
      send_datagram(dg, client->_connection);
    }
  }

  obj->announce_generate();
  assert(obj->is_do_alive());
}

/**
 *
 */
AsyncTask::DoneStatus ServerRepository::
reader_poll_task(GenericAsyncTask *task, void *data) {
  ServerRepository *self = (ServerRepository *)data;
  self->reader_poll_until_empty();
  return AsyncTask::DS_cont;
}

/**
 *
 */
AsyncTask::DoneStatus ServerRepository::
callbacks_task(GenericAsyncTask *task, void *data) {
  ServerRepository *self = (ServerRepository *)data;
  self->run_net_callbacks();
  return AsyncTask::DS_cont;
}

/**
 *
 */
AsyncTask::DoneStatus ServerRepository::
snapshot_task(GenericAsyncTask *task, void *data) {
  ServerRepository *self = (ServerRepository *)data;
  self->consider_send_snapshot(ClockObject::get_global_clock()->get_frame_count());
  return AsyncTask::DS_cont;
}

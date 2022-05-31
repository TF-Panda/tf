/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientRepository.cxx
 * @author brian
 * @date 2022-05-05
 */

#include "clientRepository.h"
#include "steamnet_includes.h"
#include "steamNetworkMessage.h"
#include "simulationManager.h"
#include "throw_event.h"
#include "distributedObject.h"
#include "clockObject.h"
#include "networkedObjectRegistry.h"
#include "networkClass.h"
#include "config_tfclient.h"
#include "tfClientBase.h"

NotifyCategoryDef(clientrepository, ":tf");

TypeHandle ClientRepository::_type_handle;

/**
 * xyz
 */
ClientRepository::
ClientRepository() :
  _net_sys(SteamNetworkSystem::get_global_ptr()),
  _connection(INVALID_STEAM_NETWORK_CONNECTION_HANDLE),
  _connected(false),
  _server_interval_per_tick(0.0),
  _server_tick_count(0),
  _delta_tick(-1),
  _client_id(-1)
{
}

/**
 *
 */
bool ClientRepository::
connect(const NetAddress &address) {
  clientrepository_cat.info()
    << "Attempting to connect to " << address << "\n";

  _server_address = address;

  _connection = _net_sys->connect_by_IP_address(address);
  if (_connection == INVALID_STEAM_NETWORK_CONNECTION_HANDLE) {
    throw_event("connect-failure");
    _server_address.clear();
    return false;
  }

  start_client_loop();

  return true;
}

/**
 *
 */
void ClientRepository::
send_hello(const std::string &password) {
  Datagram dg;
  dg.add_uint8(NM_cl_hello);
  dg.add_string(password);
  dg.add_string(player_name);
  dg.add_uint8(client_update_rate);
  dg.add_uint8(client_cmd_rate);
  send_datagram(dg);
}

/**
 *
 */
void ClientRepository::
handle_server_hello_resp(DatagramIterator &scan) {
  _client_id = scan.get_uint32();
  client_update_rate.set_value(scan.get_uint8());
  client_cmd_rate.set_value(scan.get_uint8());
  cbase->get_sim_mgr()->set_tick_rate(scan.get_uint8());

  // TEMPORARY
  Datagram dg;
  dg.add_uint8(NM_cl_level_loaded);
  send_datagram(dg);
}

/**
 *
 */
void ClientRepository::
start_client_loop() {
  // This checks that start_client_loop() isn't called more than once.
  nassertv(_reader_poll_task == nullptr);

  _reader_poll_task = new GenericAsyncTask("readerPollTask", reader_poll_task, this);
  _reader_poll_task->set_sort(-100);
  _callbacks_task = new GenericAsyncTask("netCallbacksTask", callbacks_task, this);
  _callbacks_task->set_sort(-99);
  _interp_task = new GenericAsyncTask("interpolateObjects", interp_task, this);
  _interp_task->set_sort(999); // right before igLoop.

  // Per-frame tasks.
  cbase->get_task_mgr()->add(_interp_task);

  // Per-sim tick tasks.
  cbase->get_sim_task_mgr()->add(_reader_poll_task);
  cbase->get_sim_task_mgr()->add(_callbacks_task);
}

/**
 *
 */
void ClientRepository::
stop_client_loop() {
  if (_reader_poll_task != nullptr) {
    _reader_poll_task->remove();
    _reader_poll_task = nullptr;
  }
  if (_callbacks_task != nullptr) {
    _callbacks_task->remove();
    _callbacks_task = nullptr;
  }
  if (_interp_task != nullptr) {
    _interp_task->remove();
    _interp_task = nullptr;
  }
}

/**
 *
 */
bool ClientRepository::
reader_poll_once() {
  SteamNetworkMessage msg;
  if (_net_sys->receive_message_on_connection(_connection, msg)) {
    DatagramIterator &scan = msg.get_datagram_iterator();
    NetMessage msg_type = (NetMessage)scan.get_uint8();
    handle_datagram(scan, msg_type);
    return true;
  }
  return false;
}

/**
 *
 */
void ClientRepository::
handle_datagram(DatagramIterator &scan, NetMessage msg_type) {
  switch (msg_type) {
  case NM_sv_generate_object:
    handle_generate_object(scan);
    break;
  case NM_sv_delete_object:
    handle_delete_object(scan);
    break;
  case NM_sv_tick:
    handle_server_tick(scan);
    break;
  case NM_sv_hello_resp:
    handle_server_hello_resp(scan);
    break;
  }
}

/**
 *
 */
void ClientRepository::
handle_server_tick(DatagramIterator &scan) {
  unsigned int old_tick = _server_tick_count;
  unsigned int server_tick_count = scan.get_uint32();
  _server_tick_count = server_tick_count;
  bool is_delta = (bool)scan.get_uint8();

  if (is_delta && _delta_tick < 0) {
    // We requested a full update but got a delta compressed update.
    // Ignore it.
    return;
  }

  // Temporarily update clock to match snapshot time.
  SimulationManager *sim_mgr = cbase->get_sim_mgr();
  sim_mgr->set_temp_clock(server_tick_count, server_tick_count * _server_interval_per_tick,
                          (server_tick_count - old_tick) * _server_interval_per_tick);

  bool success = unpack_server_snapshot(scan, is_delta);

  sim_mgr->restore_clock();

  if (success) {
    if (_delta_tick >= 0 || !is_delta) {
      // We have a new delta reference.
      _delta_tick = server_tick_count;
    }
  } else {
    // Couldn't unpack the state.  We need a full update.
    _delta_tick = -1;
  }

  Datagram dg;
  dg.add_uint8(NM_cl_tick);
  dg.add_int32(_delta_tick);
  send_datagram(dg);
}

/**
 *
 */
bool ClientRepository::
unpack_server_snapshot(DatagramIterator &scan, bool is_delta) {
  int num_objects = scan.get_uint16();

  pvector<DistributedObject *> objects;
  objects.reserve(num_objects);
  for (int i = 0; i < num_objects; ++i) {
    doid_t do_id = scan.get_uint32();
    DistributedObject *obj = DCAST(DistributedObject, get_object(do_id));
    if (obj != nullptr) {
      obj->pre_data_update(false);
      unpack_object_state(obj, scan);
      objects.push_back(obj);
    } else {
      return false;
    }
  }
  for (DistributedObject *obj : objects) {
    obj->post_data_update(false);
  }
  return true;
}

/**
 * Handles a message from the server to destroy one or more distributed
 * objects.
 */
void ClientRepository::
handle_delete_object(DatagramIterator &scan) {
  while (scan.get_remaining_size() > 0u) {
    doid_t do_id = scan.get_uint32();
    NetworkedObjectBase *obj = get_object(do_id);
    if (obj != nullptr) {
      delete_object(obj);
    }
  }
}

/**
 * Handles a message from the server to generate one or more distributed
 * objects.
 */
void ClientRepository::
handle_generate_object(DatagramIterator &scan) {
  NetworkedObjectRegistry *reg = NetworkedObjectRegistry::get_global_ptr();
  while (scan.get_remaining_size() > 0u) {
    unsigned int class_id = scan.get_uint16();
    doid_t do_id = scan.get_uint32();
    zoneid_t zone_id = scan.get_uint32();
    bool has_state = (bool)scan.get_uint8();
    NetworkClass *dclass = reg->get_class(class_id);
    nassertv(dclass != nullptr);
    NetworkedObjectProxy *proxy = dclass->get_linked_proxy();
    nassertv(proxy != nullptr);
    nassertv(proxy->get_object_type().is_derived_from(DistributedObject::get_class_type()));
    PT(DistributedObject) obj = DCAST(DistributedObject, proxy->make_object());
    obj->set_do_id(do_id);
    obj->set_zone_id(zone_id);
    _net_obj_table.insert({ do_id, obj });

    obj->generate();
    nassertv(obj->is_do_generated());

    if (has_state) {
      // An initial state was supplied.  Unpack it onto the object.
      obj->pre_data_update(true);
      unpack_object_state(obj, scan);
      obj->post_data_update(true);
    }

    obj->announce_generate();
    nassertv(obj->is_do_alive());
  }
}

/**
 * Unpacks a state packet from the given datagram onto the given distributed
 * object.
 */
bool ClientRepository::
unpack_object_state(DistributedObject *obj, DatagramIterator &scan) {
  NetworkClass *dclass = obj->get_network_class();

  unsigned int num_fields = scan.get_uint16();
  for (unsigned int i = 0; i < num_fields; ++i) {
    unsigned int field_num = scan.get_uint16();
    NetworkField *field = dclass->get_field(field_num);
    if (field == nullptr) {
      return false;
    }
    field->unserialize(scan, (unsigned char *)obj);
  }

  return true;
}

/**
 *
 */
void ClientRepository::
run_callbacks() {
  // This will fill up a list of connection events for us to process
  // below.
  _net_sys->run_callbacks();

  // Process the events.
  PT(SteamNetworkEvent) event = _net_sys->get_next_event();
  while (event != nullptr) {
    handle_net_callback(event->get_connection(), event->get_state(), event->get_old_state());
    event = _net_sys->get_next_event();
  }
}

/**
 *
 */
void ClientRepository::
handle_net_callback(SteamNetworkConnectionHandle connection,
                    SteamNetworkEnums::NetworkConnectionState state,
                    SteamNetworkEnums::NetworkConnectionState old_state) {
  if (connection != _connection) {
    // I don't think this is possible.. but just in case.
    return;
  }

  if (state == SteamNetworkEnums::NCS_connected) {
    // We've successfully connected.
    _connected = true;
    throw_event("connect-success");
    clientrepository_cat.info()
      << "Successfully connected to " << _server_address << "\n";
    send_hello("");

  } else if (old_state == SteamNetworkEnums::NCS_connecting) {
    // If state was connecting and the new state is not connected, we
    // failed to connect!
    _connected = false;
    clientrepository_cat.warning()
      << "Failed to connect to " << _server_address << "\n";
    _server_address.clear();
    stop_client_loop();
    throw_event("connect-failure");

  } else if (state == SteamNetworkEnums::NCS_closed_by_peer ||
             state == SteamNetworkEnums::NCS_problem_detected_locally) {
    // Lost connection.
    _connected = false;
    _server_address.clear();
    _connection = INVALID_STEAM_NETWORK_CONNECTION_HANDLE;
    clientrepository_cat.warning()
      << "Lost connection to server.\n";
    throw_event("connection-lost");
    stop_client_loop();
    delete_all_objects();
  }
}

/**
 * Destroys the given distributed object and removes it from the table.
 * Should be called when a distributed object is being removed from the world.
 */
void ClientRepository::
delete_object(NetworkedObjectBase *obj) {
  auto it = _net_obj_table.find(obj->get_do_id());
  if (it != _net_obj_table.end()) {
    _net_obj_table.erase(it);
  }
  if (obj->get_do_state() > NetworkedObjectBase::LS_disabled) {
    obj->disable();
    nassertv(obj->is_do_disabled());
  }
  obj->destroy();
  nassertv(obj->is_do_deleted());
}

/**
 * Destroys all active distributed objects visible by the client.
 * Intended to be called when leaving the game.
 */
void ClientRepository::
delete_all_objects() {
  for (auto it = _net_obj_table.begin(); it != _net_obj_table.end(); ++it) {
    NetworkedObjectBase *obj = (*it).second;
    if (obj->get_do_state() > NetworkedObjectBase::LS_disabled) {
      obj->disable();
      nassertv(obj->is_do_disabled());
    }
    obj->destroy();
    nassertv(obj->is_do_deleted());
  }

  _net_obj_table.clear();
}

/**
 *
 */
void ClientRepository::
send_datagram(const Datagram &dg, bool reliable) {
  if (dg.get_length() == 0u || !_connected) {
    return;
  }
  _net_sys->send_datagram(dg,
    reliable ? SteamNetworkEnums::NSF_reliable_no_nagle : SteamNetworkEnums::NSF_unreliable_no_delay);
}

/**
 *
 */
AsyncTask::DoneStatus ClientRepository::
reader_poll_task(GenericAsyncTask *task, void *data) {
  ClientRepository *self = (ClientRepository *)data;
  self->reader_poll_until_empty();
  return AsyncTask::DS_cont;
}

/**
 *
 */
AsyncTask::DoneStatus ClientRepository::
callbacks_task(GenericAsyncTask *task, void *data) {
  ClientRepository *self = (ClientRepository *)data;
  self->run_callbacks();
  return AsyncTask::DS_cont;
}

/**
 *
 */
AsyncTask::DoneStatus ClientRepository::
interp_task(GenericAsyncTask *task, void *data) {
  // Interpolate all DistributedObjects to current rendering time.
  ClockObject *clock = ClockObject::get_global_clock();
  DistributedObject::interpolate_objects(clock->get_frame_time());
  return AsyncTask::DS_cont;
}

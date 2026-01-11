#include "networkObject.h"
#include "gameGlobals.h"
#include "asyncTaskManager.h"

/**
 * Called when the networked object is coming into existence, before initial state
 * has been set on it.
 */
void NetworkObject::
pre_generate() {
  nassertv(is_do_new());
}

/**
 * Called when the network object is coming into existence, after initial state
 * has been set on it.
 */
void NetworkObject::
generate() {
  nassertv(is_do_new());
  _object_state = OS_alive;
}

/**
 * Called when the networked object is going away.
 */
void NetworkObject::
disable() {
  nassertv(is_do_alive());
#ifdef CLIENT
  remove_from_interp_list(this);
#endif
  remove_all_tasks();
  _object_state = OS_disabled;
}

/**
 * Sets up a task to run per rendering frame.
 */
GenericAsyncTask *NetworkObject::
add_task(const std::string &name, GenericAsyncTask::TaskFunc func, int sort) {
  remove_task(name);
  PT(GenericAsyncTask) task = new GenericAsyncTask(name);
  task->set_user_data(this);
  task->set_function(func);
  task->set_sort(sort);
  globals.task_mgr->add(task);
  _tasks.insert({ name, task });
  return task;
}

/**
 * Sets up a task to run per simulation tick.
 */
GenericAsyncTask *NetworkObject::
add_sim_task(const std::string &name, GenericAsyncTask::TaskFunc func, int sort) {
  remove_sim_task(name);
  PT(GenericAsyncTask) task = new GenericAsyncTask(name);
  task->set_user_data(this);
  task->set_function(func);
  task->set_sort(sort);
  globals.sim_task_mgr->add(task);
  _sim_tasks.insert({ name, task });
  return task;
}

/**
 * Stops a previously added per-frame task from running anymore.
 */
void NetworkObject::
remove_task(const std::string &name) {
  TaskMap::const_iterator it = _tasks.find(name);
  if (it != _tasks.end()) {
    GenericAsyncTask *task = (*it).second;
    task->remove();
    _tasks.erase(it);
  }
}

/**
 * Stops a previously added per-simulation tick task from running anymore.
 */
void NetworkObject::
remove_sim_task(const std::string &name) {
  TaskMap::const_iterator it = _sim_tasks.find(name);
  if (it != _sim_tasks.end()) {
    GenericAsyncTask *task = (*it).second;
    task->remove();
    _sim_tasks.erase(it);
  }
}

/**
 * Stops all tasks from running on the object, per-frame and per-simulation tick.
 */
void NetworkObject::
remove_all_tasks() {
  for (auto task_entry : _tasks) {
    task_entry.second->remove();
  }
  _tasks.clear();
  for (auto task_entry : _sim_tasks) {
    task_entry.second->remove();
  }
  _sim_tasks.clear();
}

#ifdef CLIENT
#include "client/client.h"
#include "client/client_config.h"
#include "client/prediction.h"

pset<NetworkObject *> NetworkObject::_interp_list;

/**
 *
 */
float NetworkObject::
get_interpolate_amount() const {
  if (_predictable) {
    return globals.cr->get_tick_interval();
  }
  int server_tick_multiple = 1;
  return globals.cr->ticks_to_time(globals.cr->time_to_ticks(get_client_interp_amount()) + server_tick_multiple);
}

/**
 * Records the current values for interpolated variables on this object for the
 * given time.
 */
void NetworkObject::
record_values_for_interpolation(float time, unsigned int flags) {
  bool update_last_networked = (flags & IVF_omit_update_last_networked) == 0;

  for (InterpolatedVarEntry &entry : _interp_vars) {
    if ((entry.flags & flags) == 0) {
      continue;
    }

    if ((entry.flags & IVF_exclude_auto_latch) != 0) {
      continue;
    }

    if (entry.var->record_value(time, update_last_networked)) {
      entry.needs_interpolation = true;
    }
  }

  add_to_interp_list(this);
}

/**
 * Resets all interpolated variables to the current values stored on the object.
 */
void NetworkObject::
reset_interpolated_vars() {
  for (InterpolatedVarEntry &entry : _interp_vars) {
    entry.var->reset();
  }
}

/**
 *
 */
void NetworkObject::
store_last_networked_value() {
  float time = GameClient::ptr()->get_client_time();
  for (InterpolatedVarEntry &entry: _interp_vars) {
    if ((entry.flags & IVF_exclude_auto_latch) != 0) {
      continue;
    }
    entry.var->record_last_networked_value(time);
  }
}

/**
 *
 */
void NetworkObject::
pre_data_update() {
  // Restore all of our interpolated variables to the most recently
  // networked value.  This way if the value does not change in the new
  // snapshot, we record the networked value, and not the most recently
  // interpolated value.  However, we only want to do this if the object
  // is actually generated and we have a previously received networked
  // value.
  if (is_do_alive()) {
    for (InterpolatedVarEntry &entry : _interp_vars) {
      entry.var->copy_last_networked_value();
    }
  }

}

/**
 *
 */
void NetworkObject::
post_data_update() {
  if (_interp_vars.empty()) {
    return;
  }

  if (!_predictable) {
    GameClient *cl = GameClient::ptr();
    float time = cl->get_client_time();
    // If we're not predicting this object, record current values into interpolation buffer.
    record_values_for_interpolation(time, InterpVarFlags::IVF_simulation);
  } else {
    // We're predicting this object.  Note the most recently networked values (the values we just got).
    store_last_networked_value();
  }
}

/**
 *
 */
void NetworkObject::
pre_interpolate() {
}

/**
 *
 */
void NetworkObject::
interpolate(float time) {
  if (_predictable) {
    // Fixup time for interpolating prediction results.
    Prediction *pred = Prediction::ptr();
    time = pred->final_predicted_tick * globals.cr->get_tick_interval();
    time -= globals.cr->get_tick_interval();
    time += globals.cr->get_simulation_delta_no_remainder();
    time += globals.cr->get_remainder();
  }

  bool done = true;
  if (time < _last_interpolation_time) {
    // Went back in time, interpolate everything.
    for (InterpolatedVarEntry &entry : _interp_vars) {
      entry.needs_interpolation = true;
    }
  }

  _last_interpolation_time = time;

  for (InterpolatedVarEntry &entry : _interp_vars) {
    if (!entry.needs_interpolation) {
      continue;
    }

    if ((entry.flags & IVF_exclude_auto_interpolate) != 0) {
      // We don't want to automatically interpolate this var.
      continue;
    }

    int ret = entry.var->interpolate_into(time);
    if (ret == 1) {
      entry.needs_interpolation = false;
    } else {
      done = false;
    }
  }

  if (done) {
    remove_from_interp_list(this);
  }
}

/**
 *
 */
void NetworkObject::
post_interpolate() {
}

/**
 *
 */
void NetworkObject::
add_to_interp_list(NetworkObject *obj) {
  _interp_list.insert(obj);
}

/**
 *
 */
void NetworkObject::
remove_from_interp_list(NetworkObject *obj) {
  auto it = _interp_list.find(obj);
  if (it != _interp_list.end()) {
    _interp_list.erase(it);
  }
}

/**
 * Interpolates all networked objects needing interpolation for the current
 * rendering time.
 */
void NetworkObject::
interpolate_objects() {
  GameClient *cl = GameClient::ptr();

  InterpolationContext ctx;
  ctx.enable_extrapolation(true);
  ctx.set_last_timestamp(cl->network_to_client_time(cl->get_last_server_tick_time()));

  // Make a copy of the interp set as objects may remove themselves from the live list.
  pset<NetworkObject *> interp_list = _interp_list;
  for (NetworkObject *obj : interp_list) {
    obj->pre_interpolate();
    obj->interpolate(cl->get_client_frame_time());
    obj->post_interpolate();
  }
}

#endif

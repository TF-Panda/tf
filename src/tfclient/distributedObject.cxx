/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedObject.cxx
 * @author brian
 * @date 2022-05-18
 */

#include "distributedObject.h"

TypeHandle DistributedObject::_type_handle;
DistributedObject::InterpList DistributedObject::_interp_list;

/**
 * xyz
 */
DistributedObject::
DistributedObject() :
  _last_interp_time(0.0)
{
}

/**
 *
 */
void DistributedObject::
disable() {
  remove_from_interpolation_list();
  NetworkedObjectBase::disable();
}

/**
 * Adds a new interpolated variable to the DistributedObject, linked to the
 * indicated data pointer.
 *
 * Values received on the wire for this variable will be recorded and
 * interpolated, with results copied to the data pointer.
 */
void DistributedObject::
add_interpolated_var(InterpolatedVariableBase *var, void *data, const std::string &name, unsigned int flags) {
#ifndef NDEBUG
  // Protect against duplicate entries.
  int idx = find_interpolated_var(var);
  nassertv(idx == -1);
  idx = find_interpolated_var(name);
  nassertv(idx == -1);
  idx = find_interpolated_var(data);
  nassertv(idx == -1);
#endif

  InterpVarEntry entry;
  entry._interp_var = var;
  entry._data = data;
  entry._name = name;
  entry._flags = flags;
  entry._needs_interpolation = false;
  _interp_vars.push_back(std::move(entry));
}

/**
 * Interpolates all variables needing interpolation to the indicated time,
 * and stores the interpolated values on the object.
 */
bool DistributedObject::
interpolate(double now, bool remove_if_done) {
  bool done = true;
  if (now < _last_interp_time) {
    for (InterpVarEntry &entry : _interp_vars) {
      entry._needs_interpolation = true;
    }
  }

  _last_interp_time = now;

  for (InterpVarEntry &entry : _interp_vars) {
    if (!entry._needs_interpolation) {
      continue;
    }

    if ((entry._flags & IV_no_auto_interp) != 0u) {
      continue;
    }

    if (entry._interp_var->interpolate_into(now, entry._data)) {
      entry._needs_interpolation = false;
    } else {
      done = false;
    }
  }

  if (done && remove_if_done) {
    remove_from_interpolation_list();
  }

  return done;
}

/**
 *
 */
void DistributedObject::
record_interp_var_values(double timestamp, unsigned int flags) {
  bool update_last_networked = (flags & IV_no_update_last_networked) == 0u;
  bool any_needs_interp = false;
  for (InterpVarEntry &entry : _interp_vars) {
    if ((entry._flags & IV_no_auto_record) != 0u) {
      continue;
    }
    if (entry._interp_var->record_void_value(entry._data, timestamp, update_last_networked)) {
      entry._needs_interpolation = true;
      any_needs_interp = true;
    }
  }
  if (any_needs_interp) {
    add_to_interpolation_list();
  }
}

/**
 *
 */
void DistributedObject::
store_last_networked_values() {
  ClockObject *clock = ClockObject::get_global_clock();
  double timestamp = clock->get_frame_time();
  for (InterpVarEntry &entry : _interp_vars) {
    if (entry._flags & IV_no_auto_record) {
      continue;
    }

    entry._interp_var->record_last_networked_void_value(entry._data, timestamp);
  }
}

/**
 * Static method that interpolates all objects in the interpolate list
 * to the given time.  Removes objects from the interpolate list that are
 * finished interpolating.
 */
void DistributedObject::
interpolate_objects(double time) {
  for (InterpList::const_iterator it = _interp_list.begin(); it != _interp_list.end();) {
    WPT(DistributedObject) obj = *it;

#ifndef NDEBUG
    if (!obj.is_valid_pointer()) {
      nassert_raise("Deleted DistributedObject found in interp list!");
      it = _interp_list.erase(it);
      continue;
    }
#endif

    if (obj->interpolate(time, false)) {
      // Finished interpolating.
      it = _interp_list.erase(it);
    } else {
      ++it;
    }
    obj->post_interpolate();
  }
}

/**
 * Called after the object has been interpolated.  Can be overridden to perform
 * any post-interpolation logic, such as syncing a node to an interpolated
 * position.
 */
void DistributedObject::
post_interpolate() {
}

/**
 * Called before unpacking new state information onto the object.
 * If generate is true, this is the initial state information of the object.
 */
void DistributedObject::
pre_data_update(bool generate) {
  NetworkedObjectBase::pre_data_update(generate);

  // Before unpacking the new state information, restore all of our
  // interpolated variables to the most recently networked value.  This way
  // if the value does not change in the new snapshot, we record the networked
  // value, and not the most recently interpolated value.  However, we only
  // want to do this if the object is actually generated and we have a
  // previously received networked value.
  if (!generate) {
    for (InterpVarEntry &entry : _interp_vars) {
      entry._interp_var->copy_last_networked_value(entry._data);
    }
  }
}

/**
 * Called after unpacking new state information onto the object.
 * If generate is true, this is a new object, and the initial state was just
 * unpacked.
 */
void DistributedObject::
post_data_update(bool generate) {
  NetworkedObjectBase::post_data_update(generate);
  if (!is_predicted()) {
    // Regular interpolation.  Record new values.
    ClockObject *clock = ClockObject::get_global_clock();
    record_interp_var_values(clock->get_frame_time(), 0u);
  } else {
    // We received prediction results.  Store the networked values
    // in our interpolated variables.
    store_last_networked_values();
  }
}

/**
 * Should return true if the DistributedObject is being predicted by the
 * client.
 */
bool DistributedObject::
is_predicted() const {
  return false;
}

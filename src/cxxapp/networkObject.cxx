#include "networkObject.h"

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
  _object_state = OS_disabled;
}

#ifdef CLIENT

/**
 * Records the current values for interpolated variables on this object for the
 * given time.
 */
void NetworkObject::
record_values_for_interpolation(float time, unsigned int flags) {
  bool update_last_networked = (flags & IVF_omit_update_last_networked) != 0;

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
  float time = 0.0f;
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
    // If we're not predicting this object, record current values into interpolation buffer.
    record_values_for_interpolation(0.0f, 0);
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
}

/**
 *
 */
void NetworkObject::
post_interpolate() {
}

#endif

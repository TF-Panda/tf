/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedObject.I
 * @author brian
 * @date 2022-05-18
 */

/**
 * Returns the number of interpolates variables on this DistributedObject.
 */
INLINE int DistributedObject::
get_num_interpolated_vars() const {
  return (int)_interp_vars.size();
}

/**
 * Returns the nth interpolated variable on this DistributedObject.
 */
INLINE DistributedObject::InterpVarEntry *DistributedObject::
get_interpolated_var(int n) {
  nassertr(n >= 0 && n < (int)_interp_vars.size(), nullptr);
  return &_interp_vars[n];
}

/**
 * Removes the interpolated variable at the indicated index.
 */
INLINE void DistributedObject::
remove_interpolated_var(int n) {
  nassertv(n >= 0 && n < (int)_interp_vars.size());
  _interp_vars.erase(_interp_vars.begin() + n);
}

/**
 * Returns the index of the interpolated variable with the indicated name,
 * or -1 if no interpolated variable has that name.
 */
INLINE int DistributedObject::
find_interpolated_var(const std::string &name) const {
  InterpolatedVars::const_iterator it = std::find_if(_interp_vars.begin(), _interp_vars.end(),
    [name] (const InterpVarEntry &entry) {
      return entry._name == name;
    });
  if (it != _interp_vars.end()) {
    return (int)(it - _interp_vars.begin());
  }
  return -1;
}

/**
 * Returns the index of the given interpolated variable, or -1 if no
 * such interpolated variable exists.
 */
INLINE int DistributedObject::
find_interpolated_var(const InterpolatedVariableBase *interp_var) const {
  InterpolatedVars::const_iterator it = std::find_if(_interp_vars.begin(), _interp_vars.end(),
    [interp_var] (const InterpVarEntry &entry) {
      return entry._interp_var == interp_var;
    });
  if (it != _interp_vars.end()) {
    return (int)(it - _interp_vars.begin());
  }
  return -1;
}

/**
 * Returns the index of the interpolated variable linked to the given data
 * pointer, or -1 if no variable is linked to that data pointer.
 */
INLINE int DistributedObject::
find_interpolated_var(void *data) const {
  InterpolatedVars::const_iterator it = std::find_if(_interp_vars.begin(), _interp_vars.end(),
    [data] (const InterpVarEntry &entry) {
      return entry._data == data;
    });
  if (it != _interp_vars.end()) {
    return (int)(it - _interp_vars.begin());
  }
  return -1;
}

/**
 *
 */
INLINE void DistributedObject::
add_to_interpolation_list() {
  _interp_list.insert(this);
}

/**
 *
 */
INLINE void DistributedObject::
remove_from_interpolation_list() {
  _interp_list.erase(this);
}

/**
 *
 */
INLINE void DistributedObject::
clear_interp_list() {
  _interp_list.clear();
}

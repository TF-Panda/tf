/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkRepository.I
 * @author brian
 * @date 2022-05-05
 */

/**
 * Returns the NetworkedObject with the indicated network ID, or NULL if no
 * such object exists.
 */
INLINE NetworkedObjectBase *NetworkRepository::
get_object(uint32_t id) const {
  ObjectTable::const_iterator it = _net_obj_table.find(id);
  if (it != _net_obj_table.end()) {
    return (*it).second;
  } else {
    return nullptr;
  }
}

/**
 * Returns true if a NetworkedObject with the indicated network ID exists
 * in the repository, or false otherwise.  This is the same as
 * get_object(id) != nullptr.
 */
INLINE bool NetworkRepository::
has_object(uint32_t id) const {
  return _net_obj_table.find(id) != _net_obj_table.end();
}

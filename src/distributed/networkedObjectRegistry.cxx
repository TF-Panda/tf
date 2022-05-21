/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkedObjectRegistry.cxx
 * @author brian
 * @date 2022-05-05
 */

#include "networkedObjectRegistry.h"
#include "networkClass.h"

NetworkedObjectRegistry *NetworkedObjectRegistry::_global_ptr = nullptr;

/**
 *
 */
void NetworkedObjectRegistry::
register_class(NetworkClass *cls) {
  if (_classes_by_name.find(cls->get_name()) != _classes_by_name.end()) {
    // Already registered.
    return;
  }

  _classes_by_name[cls->get_name()] = cls;
  cls->set_id(_ordered_classes.size());
  _ordered_classes.insert_unique(cls);
}

/**
 * Re-sorts the list of NetworkClasses by their IDs.  This is called on the
 * client after synchronizing NetworkClass IDs with the server, as the
 * server's NetworkClasses may be ordered differently.
 */
void NetworkedObjectRegistry::
sort_classes() {
  _ordered_classes.sort_unique();
}

/**
 *
 */
size_t NetworkedObjectRegistry::
get_hash() const {
  size_t hash = 0u;
  //for ()
  return hash;
}

/**
 *
 */
void NetworkedObjectRegistry::
output(std::ostream &out) const {
  for (NetworkClass *cls : _ordered_classes) {
    cls->output(out);
  }
}

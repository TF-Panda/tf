/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkedObjectRegistry.I
 * @author brian
 * @date 2022-05-05
 */

/**
 *
 */
INLINE NetworkedObjectRegistry *NetworkedObjectRegistry::
get_global_ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new NetworkedObjectRegistry;
  }
  return _global_ptr;
}

/**
 * Returns the number of registered NetworkClasses.
 */
INLINE size_t NetworkedObjectRegistry::
get_num_classes() const {
  return _ordered_classes.size();
}

/**
 * Returns the nth NetworkClass.  The index is the same as the
 * NetworkClass ID.
 */
INLINE NetworkClass *NetworkedObjectRegistry::
get_class(size_t n) const {
  nassertr(n < _ordered_classes.size(), nullptr);
  return _ordered_classes[n];
}

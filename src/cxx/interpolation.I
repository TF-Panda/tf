/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file interpolation.I
 * @author brian
 * @date 2022-05-25
 */

/**
 *
 */
INLINE void InterpolatedObject::
add_to_interpolation_list() {
  _interp_list.insert(this);
}

/**
 *
 */
INLINE void InterpolatedObject::
remove_from_interpolation_list() {
  _interp_list.erase(this);
}

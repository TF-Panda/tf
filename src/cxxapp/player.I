/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file player.I
 * @author brian
 * @date 2024-08-31
 */

/**
 *
 */
INLINE LVecBase3 Player::
get_view_angles() const {
  return _view_angles;
}

/**
 *
 */
INLINE LPoint3 Player::
get_eye_offset() const {
  return _eye_position;
}

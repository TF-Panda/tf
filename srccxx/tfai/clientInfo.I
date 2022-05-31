/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientInfo.I
 * @author brian
 * @date 2022-05-06
 */

/**
 *
 */
INLINE bool ClientInfo::
needs_update(PN_stdfloat time) const {
  return (_state > CS_unverified) && (_next_update_time <= time);
}

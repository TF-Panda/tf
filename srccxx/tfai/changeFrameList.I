/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file changeFrameList.I
 * @author lachbr
 * @date 2020-09-13
 */

/**
 * Returns the number of fields in the list.
 */
INLINE int ChangeFrameList::
get_num_fields() const {
  return (int)_change_ticks.size();
}

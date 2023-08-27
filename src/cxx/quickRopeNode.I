/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file quickRopeNode.I
 * @author brian
 * @date 2023-08-27
 */

/**
 *
 */
INLINE void QuickRopeNode::
set_point(int n, const LPoint3 &point) {
  nassertv(n >= 0 && n < (int)_points.size());
  _points[n] = point;
}

/**
 *
 */
INLINE void QuickRopeNode::
finish_modify_points() {
  recompute_interpolated_points();
  mark_internal_bounds_stale();
}

/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedEntity_src.I
 * @author brian
 * @date 2022-05-21
 */

/**
 *
 */
INLINE NodePath CLP(DistributedEntity)::
get_node() const {
  return _node;
}

/**
 *
 */
INLINE void CLP(DistributedEntity)::
set_pos(const LPoint3 &pos) {
  _pos = pos;
  _node.set_pos(pos);
}

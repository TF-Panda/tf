/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file entity.I
 * @author brian
 * @date 2024-08-31
 */

/**
 *
 */
INLINE int Entity::
get_health() const {
  return _health;
}

/**
 *
 */
INLINE int Entity::
get_max_health() const {
  return _max_health;
}

INLINE void Entity::
set_pos(const LPoint3 &pos) {
  set_transform(get_transform()->set_pos(pos));
}

INLINE LPoint3 Entity::
get_pos() const {
  return get_transform()->get_pos();
}

INLINE void Entity::
set_hpr(const LVecBase3 &hpr) {
  set_transform(get_transform()->set_hpr(hpr));
}

INLINE LVecBase3 Entity::
get_hpr() const {
  return get_transform()->get_hpr();
}

INLINE void Entity::
set_abs_pos(const LPoint3 &pos) {
  _self_path.set_pos(NodePath(), pos);
}

INLINE NodePath Entity::
get_path() const {
  return _self_path;
}

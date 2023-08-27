/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file ropePhysics.I
 * @author brian
 * @date 2023-08-13
 */

/**
 *
 */
INLINE RopePhysicsSimulation::
RopePhysicsSimulation() :
  _time_step(1.0f / 50.0f),
  _predicted_time(0.0f),
  _tick(0),
  _current_gust_timer(0.0f),
  _current_gust_lifetime(0.0f),
  _time_to_next_gust(0.0f),
  _wind_dir(LVector3::forward()),
  _wind_accel(LVector3(0)),
  _gravity(LVector3(0, 0, -1500)),
  _nurbs(nullptr),
  _quick_rope(nullptr)
{
}

/**
 *
 */
INLINE void RopePhysicsSimulation::
set_nurbs_curve(NurbsCurveEvaluator *nurbs) {
  nassertv(nurbs->get_num_vertices() == (int)_nodes.size());
  _nurbs = nurbs;
}

/**
 *
 */
INLINE void RopePhysicsSimulation::
set_quick_rope(QuickRopeNode *rope) {
  nassertv(rope->get_num_points() == (int)_nodes.size());
  _quick_rope = rope;
}

/**
 *
 */
INLINE const RopePhysicsNode *RopePhysicsSimulation::
get_node(int n) const {
  nassertr(n >= 0 && n < (int)_nodes.size(), nullptr);
  return &_nodes[n];
}

/**
 *
 */
INLINE const RopePhysicsConstraint *RopePhysicsSimulation::
get_spring(int n) const {
  nassertr(n >= 0 && n < (int)_constraints.size(), nullptr);
  return &_constraints[n];
}

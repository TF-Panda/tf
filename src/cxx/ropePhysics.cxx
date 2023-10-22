/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file ropePhysics.cxx
 * @author brian
 * @date 2023-08-13
 */

#include "ropePhysics.h"
#include "cmath.h"
#include "mathNumbers.h"
#include "jobSystem.h"

/**
 *
 */
int RopePhysicsSimulation::
add_node(const LPoint3 &pos, bool fixed) {
  RopePhysicsNode node(pos);
  node.set_fixed(fixed);
  int index = (int)_nodes.size();
  _nodes.push_back(std::move(node));
  return index;
}

/**
 *
 */
void RopePhysicsSimulation::
gen_springs(PN_stdfloat spring_dist) {
  for (int i = 1; i < (int)_nodes.size(); ++i) {
    RopePhysicsConstraint spring(i - 1, i);
    spring.set_spring_dist(spring_dist);
    _constraints.push_back(std::move(spring));
  }
}

/**
 *
 */
PN_stdfloat RopePhysicsSimulation::
get_time() const {
  return _time_step * _tick;
}

/**
 *
 */
void RopePhysicsSimulation::
update_wind(PN_stdfloat dt) {
  if (_current_gust_timer < _current_gust_lifetime) {
    PN_stdfloat div = _current_gust_timer / _current_gust_lifetime;
    PN_stdfloat scale = 1.0f - ccos(div * MathNumbers::pi);
    _wind_accel = _wind_dir * scale;
  } else {
    _wind_accel = LVector3::zero();
  }

  _current_gust_timer += dt;
  _time_to_next_gust -= dt;
  if (_time_to_next_gust <= 0.0f) {

    // Pick random wind direction.
    _wind_dir = LVector3(
      _random.random_real_unit() * 2.0f,
      _random.random_real_unit() * 2.0f,
      _random.random_real_unit() * 2.0f
    ).normalized();

    _wind_dir *= 50.0f;
    _wind_dir *= _random.random_real_unit() * 2.0f;

    _current_gust_timer = 0.0f;
    // 2-3 seconds.
    _current_gust_lifetime = _random.random_real(1.0f) + 2.0f;
    // 3-4 seconds.
    _time_to_next_gust = _random.random_real(1.0f) + 3.0f;
  }
}

/**
 * Returns the forces acting on the given node.
 */
LVector3 RopePhysicsSimulation::
get_node_forces(const RopePhysicsNode *node) const {
  if (node->get_fixed()) {
    return LVector3::zero();
  }

  LVector3 accel = _gravity;
  accel += _wind_accel;
  return accel;
}

/**
 *
 */
void RopePhysicsSimulation::
constraint_iter() {
  for (int i = 0; i < (int)_constraints.size(); ++i) {
    const RopePhysicsConstraint *spring = &_constraints[i];
    RopePhysicsNode *node_a = &_nodes[spring->get_node_a()];
    RopePhysicsNode *node_b = &_nodes[spring->get_node_b()];

    LVector3 to = node_a->get_pos() - node_b->get_pos();
    PN_stdfloat dist = to.length();

    if (dist > spring->get_spring_dist()) {
      to *= 1.0f - (spring->get_spring_dist() / dist);
      if (node_a->get_fixed()) {
        node_b->set_pos(node_b->get_pos() + to);

      } else if (node_b->get_fixed()) {
        node_a->set_pos(node_a->get_pos() - to);

      } else {
        node_a->set_pos(node_a->get_pos() - (to * 0.5f));
        node_b->set_pos(node_b->get_pos() + (to * 0.5f));
      }
    }
  }
}

/**
 *
 */
void RopePhysicsSimulation::
apply_constraints() {
  for (int i = 0; i < 3; ++i) {
    constraint_iter();
  }
}

/**
 *
 */
void RopePhysicsSimulation::
simulate(PN_stdfloat dt, PN_stdfloat damping) {
  update_wind(dt);

  _predicted_time += dt;
  int new_tick = (int)cceil(_predicted_time / _time_step);
  int num_ticks = new_tick - _tick;

  PN_stdfloat time_step_mul = _time_step * _time_step * 0.5f;

  for (int i = 0; i < num_ticks; ++i) {
    for (int j = 0; j < (int)_nodes.size(); ++j) {
      RopePhysicsNode *node = &_nodes[j];
      LVector3 accel = get_node_forces(node);
      LPoint3 prev_pos = node->get_pos();
      node->set_pos(node->get_pos() + (node->get_pos() - node->get_prev_pos()) * damping + accel * time_step_mul);
      node->set_prev_pos(prev_pos);
    }
    apply_constraints();
  }

  _tick = new_tick;

  PN_stdfloat interpolant = (_predicted_time - (get_time() - _time_step)) / _time_step;
  for (RopePhysicsNode &node : _nodes) {
    node.set_smooth_pos(node.get_prev_pos() + (node.get_pos() - node.get_prev_pos()) * interpolant);
  }

  // Update NURBS curve if we have one.
  if (_nurbs != nullptr) {
    for (int i = 0; i < (int)_nodes.size() && i < _nurbs->get_num_vertices(); ++i) {
      _nurbs->set_vertex(i, _nodes[i].get_smooth_pos());
    }
  } else if (_quick_rope != nullptr) {
    for (int i = 0; i < (int)_nodes.size() && i < _quick_rope->get_num_points(); ++i) {
      _quick_rope->set_point(i, _nodes[i].get_smooth_pos());
    }
    _quick_rope->finish_modify_points();
  }
}

/**
 *
 */
void RopeSimulationManager::
simulate(PN_stdfloat dt, PN_stdfloat damping) {
  JobSystem *js = JobSystem::get_global_ptr();
  js->parallel_process((int)_ropes.size(), [&] (int i) {
    _ropes[i]->simulate(dt, damping);
  });
}

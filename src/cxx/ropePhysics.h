/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file ropePhysics.h
 * @author brian
 * @date 2023-08-13
 */

#ifndef ROPEPHYSICS_H
#define ROPEPHYSICS_H

#include "tfbase.h"
#include "luse.h"
#include "referenceCount.h"
#include "pointerTo.h"
#include "pvector.h"
#include "randomizer.h"
#include "nurbsCurveEvaluator.h"
#include "quickRopeNode.h"

/**
 * Defines a node/point in the rope.
 */
class EXPCL_TF_CXX RopePhysicsNode {
PUBLISHED:
  INLINE RopePhysicsNode(const LPoint3 &pos) :
    _pos(pos), _orig_pos(pos), _prev_pos(pos), _smooth_pos(pos),
    _fixed(false) { }

  INLINE void set_pos(const LPoint3 &pos) { _pos = pos; }
  INLINE LPoint3 get_pos() const { return _pos; }

  INLINE void set_orig_pos(const LPoint3 &pos) { _orig_pos = pos; }
  INLINE LPoint3 get_orig_pos() const { return _orig_pos; }

  INLINE void set_prev_pos(const LPoint3 &pos) { _prev_pos = pos; }
  INLINE LPoint3 get_prev_pos() const { return _prev_pos; }

  INLINE void set_smooth_pos(const LPoint3 &pos) { _smooth_pos = pos; }
  INLINE LPoint3 get_smooth_pos() const { return _smooth_pos; }

  INLINE void set_fixed(bool fixed) { _fixed = fixed; }
  INLINE bool get_fixed() const { return _fixed; }

private:
  LPoint3 _pos, _orig_pos, _prev_pos, _smooth_pos;

  // If true, the node stays fixed to the provided position.
  bool _fixed;
};

/**
 * Constraint between two rope nodes.
 */
class EXPCL_TF_CXX RopePhysicsConstraint {
PUBLISHED:
  INLINE RopePhysicsConstraint(int node_a, int node_b) :
    _node_a(node_a), _node_b(node_b), _spring_dist(0.0f) { }

  INLINE int get_node_a() const { return _node_a; }
  INLINE int get_node_b() const { return _node_b; }

  INLINE void set_spring_dist(PN_stdfloat dist) { _spring_dist = dist; }
  INLINE PN_stdfloat get_spring_dist() const { return _spring_dist; }

private:
  int _node_a, _node_b;
  PN_stdfloat _spring_dist;
};

/**
 * Implements basic physics simulation for ropes.
 */
class EXPCL_TF_CXX RopePhysicsSimulation : public ReferenceCount {
PUBLISHED:
  INLINE RopePhysicsSimulation();

  void simulate(PN_stdfloat dt, PN_stdfloat damping);

  int add_node(const LPoint3 &pos, bool fixed);
  void gen_springs(PN_stdfloat spring_dist);

  INLINE void set_nurbs_curve(NurbsCurveEvaluator *nurbs);
  INLINE NurbsCurveEvaluator *get_nurbs_curve() const { return _nurbs; }

  INLINE void set_quick_rope(QuickRopeNode *rope);
  INLINE QuickRopeNode *get_quick_rope() const { return _quick_rope; }

  INLINE int get_num_nodes() const { return (int)_nodes.size(); }
  INLINE const RopePhysicsNode *get_node(int n) const;

  INLINE int get_num_springs() const { return (int)_constraints.size(); }
  INLINE const RopePhysicsConstraint *get_spring(int n) const;

  INLINE void set_time_step(PN_stdfloat step) { _time_step = step; }
  INLINE PN_stdfloat get_time_step() const { return _time_step; }

  INLINE void set_gravity(LVector3 gravity) { _gravity = gravity; }
  INLINE LVector3 get_gravity() const { return _gravity; }

private:
  LVector3 get_node_forces(const RopePhysicsNode *node) const;
  void constraint_iter();
  void apply_constraints();
  void update_wind(PN_stdfloat dt);
  PN_stdfloat get_time() const;

private:
  typedef pvector<RopePhysicsNode> Nodes;
  typedef pvector<RopePhysicsConstraint> Constraints;

  Nodes _nodes;
  Constraints _constraints;

  // Simulation time.
  PN_stdfloat _predicted_time;
  PN_stdfloat _time_step;
  unsigned int _tick;

  // Variables to implement rope swaying in wind.
  PN_stdfloat _current_gust_timer;
  PN_stdfloat _current_gust_lifetime;
  PN_stdfloat _time_to_next_gust;
  LVector3 _wind_dir;
  LVector3 _wind_accel;

  LVector3 _gravity;

  Randomizer _random;

  // Optional NURBS curve with vertices synchronized to the rope node positions.
  PT(NurbsCurveEvaluator) _nurbs;
  PT(QuickRopeNode) _quick_rope;
};

class EXPCL_TF_CXX RopeSimulationManager : public MemoryBase {
PUBLISHED:
  INLINE RopeSimulationManager() = default;

  void simulate(PN_stdfloat dt, PN_stdfloat damping);

  INLINE void remove_rope(RopePhysicsSimulation *rope);
  INLINE void add_rope(RopePhysicsSimulation *rope);

private:
  pvector<PT(RopePhysicsSimulation)> _ropes;
};

#include "ropePhysics.I"

#endif // ROPEPHYSICS_H

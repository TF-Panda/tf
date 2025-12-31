/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file entity.h
 * @author brian
 * @date 2024-08-31
 */

#ifndef ENTITY_H
#define ENTITY_H

#include "typedObject.h"
#include "typeHandle.h"
#include "pandaNode.h"
#include "nodePath.h"
#include "networkObject.h"
#include "interpolatedVariable.h"

class NetworkClass;

/**
 * Base entity class.
 */
class Entity : public NetworkObject {
public:
  Entity(const std::string &name = "");

  INLINE int get_health() const;
  INLINE int get_max_health() const;

  INLINE void set_pos(const LPoint3 &pos);
  INLINE LPoint3 get_pos() const;

  INLINE void set_hpr(const LVecBase3 &hpr);
  INLINE LVecBase3 get_hpr() const;

  INLINE void set_abs_pos(const LPoint3 &pos);
  INLINE LPoint3 get_abs_pos() const;

  INLINE void set_abs_hpr(const LVecBase3 &hpr);
  INLINE LVecBase3 get_abs_hpr() const;

  INLINE NodePath get_node_path() const;

  inline bool is_dead() const;

  virtual void generate() override;
  virtual void disable() override;

private:
  static void s_set_pos(LVecBase3f pos, void *ent);
  static LVecBase3f s_get_pos(void *ent);
  static void s_set_hpr(LVecBase3f hpr, void *ent);
  static LVecBase3f s_get_hpr(void *ent);

protected:
  std::string _name;
  int _health;
  int _max_health;
  int _parent_entity;
  int _team;
  LVector3 _view_offset;

  // Path to node representing this entity.
  NodePath _node_path;

#ifdef CLIENT
  PT(InterpolatedVec3f) _iv_pos;
  PT(InterpolatedVec3f) _iv_hpr;
#endif

public:
  virtual NetworkClass *get_network_class() const override {
    return _network_class;
  }
  inline static NetworkClass *get_type_network_class() {
    return _network_class;
  }
  static void init_network_class();
protected:
  static NetworkClass *_network_class;
};

/**
 * Is the entity dead? Based on hp.
 */
inline bool Entity::
is_dead() const {
  return _max_health > 0 && _health <= 0;
}

#include "entity.I"

#endif // ENTITY_H

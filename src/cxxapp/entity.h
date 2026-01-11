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
#include "entityCollision.h"

#ifdef CLIENT
#include "interpolatedVariable.h"
#include "client/prediction.h"
#endif

class NetworkClass;
class PDXElement;
class MapEntity;

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

  inline void set_simulation_tick(int tick);
  inline int get_simulation_tick() const;

  void initialize_collisions();
  void destroy_collisions();
  inline EntityCollision &get_collision_info();

  virtual void generate() override;
  virtual void disable() override;

  virtual void simulate();

#ifdef SERVER
  // Called when the entity is coming from the level.
  virtual void init_from_level(const MapEntity *map_ent, PDXElement *props);
#endif

#ifdef CLIENT
  virtual void post_data_update() override;
  virtual bool should_predict() const;
  void init_prediction();
  void shutdown_prediction();
  virtual void add_prediction_fields();
  template<class Type>
  inline PredictionFieldBase *add_pred_field(const std::string &name, Type *data_ptr,
					     typename PredictionFieldTempl<Type>::SetValueFn setter = nullptr,
					     typename PredictionFieldTempl<Type>::GetValueFn getter = nullptr,
					     bool networked = true, bool no_error_check = false,
					     bool is_private = false, float tolerance = 0.0f);
  void remove_pred_field(const std::string &name);
  inline PredictedObject *get_pred() const;
#endif // CLIENT

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
  int _simulation_tick;

  // Path to node representing this entity.
  NodePath _node_path;

  // Root node that physics actors for this entity live under.
  NodePath _phys_root;

  EntityCollision _collision_info;

#ifdef CLIENT
  PT(InterpolatedVec3f) _iv_pos;
  PT(InterpolatedVec3f) _iv_hpr;
  PT(PredictedObject) _pred;
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
 *
 */
inline EntityCollision &Entity::
get_collision_info() {
  return _collision_info;
}

/**
 * Is the entity dead? Based on hp.
 */
inline bool Entity::
is_dead() const {
  return _max_health > 0 && _health <= 0;
}

/**
 *
 */
inline void Entity::
set_simulation_tick(int tick) {
  _simulation_tick = tick;
}

/**
 *
 */
inline int Entity::
get_simulation_tick() const {
  return _simulation_tick;
}

#ifdef CLIENT

/**
 *
 */
template<class Type>
inline PredictionFieldBase *Entity::
add_pred_field(const std::string &name, Type *data_ptr, typename PredictionFieldTempl<Type>::SetValueFn setter,
	       typename PredictionFieldTempl<Type>::GetValueFn getter, bool networked, bool no_error_check,
	       bool is_private, float tolerance) {
  nassertr(_pred != nullptr, nullptr);
  PT(PredictionFieldTempl<Type>) field = new PredictionFieldTempl<Type>;
  field->name = name;
  field->getter = getter;
  field->setter = setter;
  field->data_ptr = data_ptr;
  field->networked = networked;
  field->no_error_check = no_error_check;
  field->is_private = is_private;
  field->tolerance = tolerance;
  _pred->fields.push_back(field);
  return field;
}

/**
 *
 */
inline PredictedObject *Entity::
get_pred() const {
  return _pred;
}

#endif

#include "entity.I"

#endif // ENTITY_H

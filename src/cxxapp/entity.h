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

class NetworkClass;

/**
 * Base entity class.
 */
class Entity : public PandaNode, public NetworkObject {
  DECLARE_CLASS(Entity, PandaNode);

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

  INLINE NodePath get_path() const;

  virtual void spawn();
  virtual void destroy();

protected:
  int _health;
  int _max_health;

  float _charge_level;

  LPoint3f _test_pos;

  // Nodepath to myself.
  NodePath _self_path;

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

#include "entity.I"

#endif // ENTITY_H

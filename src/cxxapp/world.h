/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file world.h
 * @author brian
 * @date 2024-09-01
 */

#ifndef WORLD_H
#define WORLD_H

#include "entity.h"
#include "pointerTo.h"
#include "physRigidStaticNode.h"
#include "pvector.h"
#include "entityFactory.h"

class MapModel;

class World : public Entity {
  DECLARE_CLASS(World, Entity);

public:
  World();

  virtual void spawn() override;
  virtual void destroy() override;

public:
  static Entity *create_World();
  static void register_ent_factory();

private:
  void init_world_collisions();
  void parent_model_geometry();

private:
  typedef pvector<PT(PhysRigidStaticNode)> WorldCollisionList;
  WorldCollisionList _world_collisions;

  int _model_index;
  const MapModel *_map_model;
};

#include "world.I"

#endif // WORLD_H

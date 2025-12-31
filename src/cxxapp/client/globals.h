/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file globals.h
 * @author brian
 * @date 2024-08-31
 */

#ifndef GLOBALS_H
#define GLOBALS_H

#include "mapData.h"
#include "nodePath.h"
#include "inputManager.h"
#include "physScene.h"
#include "graphicsWindow.h"

class Player;
class World;



enum CollisionGroup {
  CG_world = 1 << 0,
  CG_sky = 1 << 1,
  CG_player_clip = 1 << 2,
  CG_projectile = 1 << 3,
  CG_hitbox = 1 << 4,
  CG_debris = 1 << 5,
  CG_trigger = 1 << 6,
};

class Globals {
public:
  World *world = nullptr;
  MapData *map_data = nullptr;
  Player *local_av = nullptr;
  InputManager *input = nullptr;
  NodePath render;
  NodePath camera;
  PhysScene *physics_world = nullptr;
  GraphicsWindow *win = nullptr;
};

extern Globals *globals;

#endif // GLOBALS_H

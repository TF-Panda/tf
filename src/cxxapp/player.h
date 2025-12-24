/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file player.h
 * @author brian
 * @date 2024-08-31
 */

#ifndef PLAYER_H
#define PLAYER_H

#include "entity.h"

class Player : public Entity {
  DECLARE_CLASS(Player, Entity);

public:
  Player();

  void move_player();
  void mouse_movement();
  void apply_friction(double dt);
  void accelerate(double dt, const LVector3 &direction, float velocity);

  INLINE LVecBase3 get_view_angles() const;
  INLINE LPoint3 get_eye_offset() const;

private:
  LVector3 _velocity;
  LVecBase3 _view_angles;
  LPoint3 _eye_position;

  float _walkspeed;
  float _runspeed;
  float _max_speed;

  LVecBase2 _mouse_delta;
  LVecBase2 _last_mouse_sample;
};

#include "player.I"

#endif // PLAYER_H

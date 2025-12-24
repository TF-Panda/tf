/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file player.cxx
 * @author brian
 * @date 2024-08-31
 */

#include "player.h"
#include "clockObject.h"
#include "globals.h"
#include "inputManager.h"
#include "configVariableDouble.h"
#include "graphicsWindowInputDevice.h"

static ConfigVariableDouble mouse_sensitivity("mouse-sensitivity", 5.0);

static constexpr float move_friction = 4.0f;
static constexpr float move_accel = 10.0f;
static constexpr float move_stop_speed = 100.0f;

TypeHandle Player::_type_handle;

/**
 *
 */
Player::
Player() :
  Entity("player"),
  _velocity(0.0f),
  _walkspeed(150.0f),
  _runspeed(250.0f),
  _max_speed(250.0f),
  _last_mouse_sample(0.0f),
  _mouse_delta(0.0f),
  _view_angles(0.0f),
  _eye_position(0.0f, 0.0f, 64.0f)
{
  _max_speed = _walkspeed;
}

/**
 *
 */
void Player::
mouse_movement() {
  float sens = mouse_sensitivity.get_value();

  // Query the current mouse location from the graphics window.
  // TODO: Handle a gamepad?
  GraphicsWindowInputDevice *win_input_device;
  DCAST_INTO_V(win_input_device, globals->win->get_input_device(0));
  PointerData pd = win_input_device->get_pointer();

  LVecBase2 sample(pd.get_x(), -pd.get_y());
  LVecBase2 delta = (sample - _last_mouse_sample) * sens;
  _view_angles[0] -= delta.get_x() * 0.022f;
  _view_angles[1] = std::clamp(_view_angles[1] + (delta.get_y() * 0.022f), -89.0f, 89.0f);
  _view_angles[2] = 0.0f;
  _mouse_delta += delta;
  _last_mouse_sample = sample;
}

/**
 *
 */
void Player::
apply_friction(double dt) {
  // Apply friction.
  float speed = _velocity.length();
  if (speed > 0.1f) {
    float friction = move_friction;
    float control = speed < move_stop_speed ? move_stop_speed : speed;
    float drop = friction * control * dt;
    float new_speed = speed - drop;
    new_speed = std::max(0.0f, new_speed);
    if (new_speed != speed) {
      new_speed /= speed;
      _velocity *= new_speed;
    }
  }
}

/**
 *
 */
void Player::
accelerate(double dt, const LVector3 &direction, float velocity) {
  // Accelerate.
  float current_speed = _velocity.dot(direction);
  float add_speed = velocity - current_speed;
  if (add_speed > 0.0f) {
    float accel_speed = move_accel * dt * velocity;
    accel_speed = std::min(add_speed, accel_speed);
    _velocity += direction * accel_speed;
  }
}

/**
 *
 */
void Player::
move_player() {
  // Apply mouse movement to view angles.
  mouse_movement();

  ClockObject *clock = ClockObject::get_global_clock();
  double dt = clock->get_dt();

  InputManager *input = globals->input;

  float fwdmove = 0.0f;
  float sidemove = 0.0f;
  if (input->get_button_value(IC_move_forward)) {
    fwdmove = _walkspeed;
  } else if (input->get_button_value(IC_move_back)) {
    fwdmove = -_walkspeed;
  }

  if (input->get_button_value(IC_move_left)) {
    sidemove = -_walkspeed;
  } else if (input->get_button_value(IC_move_right)) {
    sidemove = _walkspeed;
  }

  LVector3 moveVec(sidemove, fwdmove, 0.0f);
  float moveVel = moveVec.length();
  moveVec.normalize();

  if (moveVel > _max_speed) {
    moveVel = _max_speed;
  }

  // The movement vector above is relative to the direction the player is looking.
  // Transform by the view angles to get the world-space movement vector.
  LQuaternion view_rot;
  // Factor in just the yaw.  We don't want to fly.
  view_rot.set_hpr(LVecBase3(_view_angles[0], 0.0f, 0.0f));
  LVector3 world_move_vec = view_rot.xform(moveVec);

  apply_friction(dt);
  accelerate(dt, world_move_vec, moveVel);

  moveVel = std::min(moveVel, _max_speed);

  NodePath &np = get_node_path();
  np.set_pos(np.get_pos() + _velocity * dt);
}

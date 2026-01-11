#ifdef CLIENT

#include "clockObject.h"
#include "windowProperties.h"
#include "localTFPlayer.h"
#include "../tfPlayer.h"
#include "client.h"
#include "../gameGlobals.h"
#include "inputButtons.h"
#include "inputManager.h"
#include "randomizer.h"
#include "client_config.h"
#include "graphicsWindow.h"
#include "graphicsWindowInputDevice.h"
#include "configVariableDouble.h"
#include "configVariableBool.h"
#include "prediction.h"
#include "../weapon.h"
#include <limits>

ConfigVariableDouble mouse_sensitivity
("mouse-sensitivity", 5.0,
 PRC_DESC("Self-explanatory."));

ConfigVariableDouble controller_look_sensitivity_x
("controller-look-sensitivity-x", 100.0f,
 PRC_DESC("Degrees per-second to look when the stick is fully pushed to the left or right"));
ConfigVariableDouble controller_look_sensitivity_y
("controller-look-sensitivity-y", 100.0f,
 PRC_DESC("Degrees per-second to look when the stick is fully pushed up or down."));
ConfigVariableBool controller_look_invert_y
("controller-look-invert-y", false,
 PRC_DESC("Whether or not to invert the Y axis on controller for looking up and down."));

/**
 *
 */
LocalTFPlayer::
LocalTFPlayer(TFPlayer *player) :
  _player(player),
  _commands_sent(0),
  _last_outgoing_command(-1),
  _choked_commands(0),
  _next_command_time(0.0f),
  _current_command(nullptr),
  _final_predicted_tick(0),
  _last_mouse_sample(0.0f),
  _mouse_delta(0.0f),
  _prediction_error(0.0f),
  _prediction_error_time(0.0f),
  _controls_enabled(false)
{
}

/**
 *
 */
void LocalTFPlayer::
enable_controls() {
  if (_controls_enabled) {
    return;
  }

  WindowProperties wprops;
  wprops.set_cursor_hidden(true);
  wprops.set_mouse_mode(WindowProperties::M_relative);
  globals.win->request_properties(wprops);

  // Start deltaing from current mouse position in window if it's
  // in the window
  if (globals.input->has_mouse_in_window()) {
    int win_size_x = globals.win->get_x_size();
    int win_size_y = globals.win->get_y_size();
    LPoint2 pointer_pos = globals.input->get_mouse_in_window();
    _last_mouse_sample[0] = (pointer_pos[0] * 0.5f + 0.5f) * win_size_x;
    _last_mouse_sample[1] = (pointer_pos[1] * 0.5f + 0.5f) * win_size_y;
  } else {
    _last_mouse_sample = 0.0f;
  }

  _mouse_delta = 0.0f;
  _controls_enabled = true;
}

/**
 *
 */
void LocalTFPlayer::
disable_controls() {
  if (!_controls_enabled) {
    return;
  }
  WindowProperties wprops;
  wprops.set_cursor_hidden(false);
  wprops.set_mouse_mode(WindowProperties::M_absolute);
  globals.win->request_properties(wprops);
  _controls_enabled = false;
}

/**
 *
 */
void LocalTFPlayer::
run_controls() {
  GameClient *cl = GameClient::ptr();
  InputManager *input = globals.input;

  PlayerCommand *cmd = get_next_command();
  cmd->clear();
  cmd->command_number = get_next_command_number();
  Randomizer ran(cmd->command_number);
  cmd->random_seed = ran.random_int(std::numeric_limits<int>::max());
  cmd->tick_count = cl->get_tick_count();

  if (!_player->is_dead()) {
    cmd->view_angles = _player->_view_angles;
    cmd->mouse_delta = _mouse_delta;
    bool move_fwd_down = input->is_button_down(IB_move_forward);
    bool move_back_down = input->is_button_down(IB_move_back);
    bool move_left_down = input->is_button_down(IB_move_left);
    bool move_right_down = input->is_button_down(IB_move_right);
    if (move_fwd_down) {
      cmd->buttons |= IC_move_forward;
    }
    if (move_back_down) {
      cmd->buttons |= IC_move_back;
    }
    if (move_left_down) {
      cmd->buttons |= IC_move_left;
    }
    if (move_right_down) {
      cmd->buttons |= IC_move_right;
    }
    if (input->is_button_down(IB_jump)) {
      cmd->buttons |= IC_jump;
    }
    if (input->is_button_down(IB_duck)) {
      cmd->buttons |= IC_duck;
    }
    if (input->is_button_down(IB_primary_attack)) {
      cmd->buttons |= IC_primary_attack;
    }
    if (input->is_button_down(IB_secondary_attack)) {
      cmd->buttons |= IC_secondary_attack;
    }
    if (input->is_button_down(IB_reload)) {
      cmd->buttons |= IC_reload;
    }

    float fwd_amount = 0.0f;
    fwd_amount += move_fwd_down ? 1.0f : 0.0f;
    fwd_amount += move_back_down ? -1.0f : 0.0f;
    fwd_amount += input->get_axis(IB_axis_move_y);

    float side_amount = 0.0f;
    side_amount += move_right_down ? 1.0f : 0.0f;
    side_amount += move_left_down ? -1.0f : 0.0f;
    side_amount += input->get_axis(IB_axis_move_x);

    fwd_amount = std::clamp(fwd_amount, -1.0f, 1.0f);
    side_amount = std::clamp(side_amount, -1.0f, 1.0f);

    if (fwd_amount > 0.0f) {
      cmd->move.set_y(base_move_speed /* * class forward factor*/ * fwd_amount);
    } else {
      cmd->move.set_y(base_move_speed /* * class backward factor*/ * fwd_amount);
    }

    cmd->move.set_x(base_move_speed /* * class forward factor*/ * side_amount);
  }

  consider_send_command();

  // Reset mouse delta accumulated between sim ticks.
  _mouse_delta.set(0.0f, 0.0f);
}

/**
 * Applies mouse/controller movement to the player's view direction.
 */
void LocalTFPlayer::
sample_mouse() {

  // Check for toggling of controls.
  if (globals.input->was_button_pressed(IB_pause)) {
    if (_controls_enabled) {
      disable_controls();
    } else {
      enable_controls();
    }
  }

  bool do_movement = _controls_enabled;
  if (_player->is_dead()) {
    do_movement = false;
  }

  if (do_movement) {
    GraphicsWindow *win = globals.win;

    float sens = mouse_sensitivity;

    LVecBase2f sample = 0.0f;

    // Find a valid pointer to sample from.
    for (int i = 0; i < win->get_num_input_devices(); ++i) {
      InputDevice *device = win->get_input_device(i);
      if (device->has_pointer() && device->is_of_type(GraphicsWindowInputDevice::get_class_type())) {
	GraphicsWindowInputDevice *win_device = DCAST(GraphicsWindowInputDevice, device);
	PointerData pointer = win_device->get_pointer();
	if (pointer.get_in_window()) {
	  sample.set(pointer.get_x(), pointer.get_y());
	}
      }
    }

    sample.set_y(-sample.get_y());

    LVecBase2f delta = (sample - _last_mouse_sample) * sens;
    _mouse_delta += delta;
    delta[0] *= 0.022f;
    delta[1] *= 0.022f;

    // Also sample controller look axes.
    ClockObject *clock = ClockObject::get_global_clock();
    float dt = clock->get_dt();
    delta[0] += globals.input->get_axis(IB_axis_look_x) * controller_look_sensitivity_x * dt;
    delta[1] += globals.input->get_axis(IB_axis_look_y) * controller_look_sensitivity_y * dt *
      (controller_look_invert_y.get_value() ? -1.0f : 1.0f);

    // Update view angles from mouse sample.
    _player->_view_angles[0] -= delta[0];
    _player->_view_angles[1] += delta[1];
    _player->_view_angles[1] = std::clamp(_player->_view_angles[1], -89.0f, 89.0f);
    // No roll.
    _player->_view_angles[2] = 0.0f;

    _last_mouse_sample = sample;
  }
}

/**
 *
 */
void LocalTFPlayer::
consider_send_command() {
  GameClient *cl = GameClient::ptr();

  if (should_send_command()) {
    send_command();
    cl->send_tick();

    _last_outgoing_command = _commands_sent - 1;
    _choked_commands = 0;

    // Determine when to send next command.
    float network_time = cl->get_network_time();
    float cmd_interval = 1.0f / cl_cmd_rate;
    float max_delta = std::min(cl->get_tick_interval(), cmd_interval);
    float delta = std::max(0.0f, std::min(max_delta, network_time - _next_command_time));
    _next_command_time = network_time + cmd_interval - delta;
  } else {
    // Not sending yet, but building a list of commands to send.
    ++_choked_commands;
  }
}

/**
 *
 */
bool LocalTFPlayer::
write_command_delta(Datagram &dg, int prev, int to, bool is_new) {
  PlayerCommand null_cmd;

  PlayerCommand *f = &null_cmd;
  if (prev != -1) {
    f = get_command(prev);
    if (f == nullptr) {
      f = &null_cmd;
    }
  }

  PlayerCommand *t = get_command(to);
  if (t == nullptr) {
    t = &null_cmd;
  }

  t->write(dg, *f);

  return true;
}

/**
 *
 */
void LocalTFPlayer::
send_command() {
  int next_command_num = (int)get_next_command_number();

  PlayerCommandArgs args;

  // Send the player command message.

  int cmd_backup = 2;
  int backup_commands = std::max(0, std::min(max_backup_commands, cmd_backup));
  args.num_backup_commands = backup_commands;

  int new_commands = 1 + _choked_commands;
  new_commands = std::max(0, std::min(max_new_commands, new_commands));
  args.num_new_commands = new_commands;

  int num_cmds = new_commands + backup_commands;

  // First command is delta'd against zeros.
  int prev = -1;

  bool ok = true;

  int to = (int)next_command_num - num_cmds + 1;

  for (; to <= next_command_num; ++to) {
    bool is_new_cmd = to >= ((int)next_command_num - new_commands + 1);
    ok = ok && write_command_delta(args.data, prev, to, is_new_cmd);
    prev = to;
  }

  if (ok) {
    // Send it out!
    GameClient *cl = GameClient::ptr();
    cl->send_obj_message(_player, "player_command", &args);
    _commands_sent += new_commands;
  }
}

/**
 *
 */
int LocalTFPlayer::
get_next_command_number() const {
  return _last_outgoing_command + _choked_commands + 1;
}

/**
 *
 */
PlayerCommand *LocalTFPlayer::
get_next_command() {
  return &_commands[get_next_command_number() % max_commands];
}

/**
 *
 */
bool LocalTFPlayer::
should_send_command() const {
  GameClient *cl = GameClient::ptr();
  return cl->get_network_time() >= _next_command_time && cl->is_connected();
}

/**
 *
 */
PlayerCommand *LocalTFPlayer::
get_command(int num) {
  PlayerCommand *cmd = &_commands[num % max_commands];
  if (cmd->command_number != num) {
    return nullptr;
  }
  return cmd;
}

/**
 *
 */
void LocalTFPlayer::
calc_view() {
  globals.camera.set_pos(_player->get_pos() + _player->_view_offset);
  globals.camera.set_hpr(_player->_view_angles);
}

/**
 *
 */
void LocalTFPlayer::
simulate() {
  // Local player should only be simulated during prediction!
  Prediction *pred = Prediction::ptr();

  if (!pred->in_prediction) {
    return;
  }

  if (_player->_simulation_tick == globals.cr->get_tick_count()) {
    return;
  }

  _player->_simulation_tick = globals.cr->get_tick_count();

  if (!_cmd_ctx.needs_processing) {
    // No command to process.
    return;
  }

  _cmd_ctx.needs_processing = false;

  predict_command(_cmd_ctx.cmd);
}

/**
 * Predicts a player command on the local player.
 */
void LocalTFPlayer::
predict_command(PlayerCommand *cmd) {
  _current_command = cmd;
  // TODO: publish the random seed somewhere?

  globals.cr->enter_simulation_time(cmd->tick_count, _player->get_tick_base());

  if (!_player->is_dead()) {
    // Do weapon selection.

    // update buttons state

    LVecBase3f orig_view_angles = _player->_view_angles;

    Weapon *wpn = _player->get_active_weapon();
    if (wpn != nullptr) {
      wpn->item_pre_frame();
    }

    // RUN MOVEMENT

    float dt = globals.cr->get_delta_time();

    // Factor just yaw into move direction.
    LQuaternionf view_angle_quat;
    view_angle_quat.set_hpr(LVecBase3f(cmd->view_angles[0], 0.0f, 0.0f));
    LVector3f view_forward = view_angle_quat.get_forward();
    LVector3f view_right = view_angle_quat.get_right();
    LVector3f world_move = view_forward * cmd->move[1] + view_right * cmd->move[0];

    _player->set_pos(_player->get_pos() + world_move * dt);
    LVecBase3f hpr = _player->get_hpr();
    _player->set_hpr(LVecBase3f(_player->_view_angles[0], hpr[1], hpr[2]));

    if (wpn != nullptr) {
      wpn->item_busy_frame();
    }

    if (wpn != nullptr) {
      wpn->item_post_frame();
    }

    // Restore smooth view angles.
    _player->_view_angles = orig_view_angles;
  }

  ++_player->_tick_base;

  globals.cr->exit_simulation_time();

  _current_command = nullptr;
}

/**
 *
 */
void LocalTFPlayer::
note_prediction_error(const LVector3f &delta) {
  if (_player->is_dead()) {
    return;
  }

  LVector3f old_delta = get_prediction_error_smoothing_vector();

  // Sum all errors within smoothing time.
  _prediction_error = delta + old_delta;
  // Remember when last error happened.
  _prediction_error_time = globals.cr->get_client_time();

  _player->reset_interpolated_vars();
}

/**
 *
 */
LVector3f LocalTFPlayer::
get_prediction_error_smoothing_vector() const {
  float error_amount = (globals.cr->get_client_time() - _prediction_error_time) - 0.1f;
  if (error_amount >= 1.0f) {
    return LVector3f::zero();
  }

  error_amount = std::clamp(error_amount, 0.0f, 1.0f);
  error_amount = 1.0f - error_amount;

  return _prediction_error * error_amount;
}

#endif // CLIENT

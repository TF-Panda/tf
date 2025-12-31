#ifdef CLIENT

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
#include <limits>

ConfigVariableDouble mouse_sensitivity
("mouse-sensitivity", 5.0,
 PRC_DESC("Self-explanatory."));

/**
 *
 */
LocalTFPlayer::
LocalTFPlayer(TFPlayer *player) :
  _player(player),
  _commands_sent(0),
  _last_outgoing_command(-1),
  _command_ack(0),
  _last_command_ack(0),
  _choked_commands(0),
  _next_command_time(0.0f),
  _current_command(nullptr),
  _final_predicted_tick(0),
  _last_mouse_sample(0.0f),
  _mouse_delta(0.0f),
  _prediction_error(0.0f),
  _prediction_error_time(0.0f)
{
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
 *
 */
void LocalTFPlayer::
sample_mouse() {
  bool do_movement = true;
  // TODO: if dead don't do mouse movement

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

    // Update view angles from mouse sample.
    _player->_view_angles[0] -= delta[0] * 0.022f;
    _player->_view_angles[1] = std::clamp(-89.0f, 89.0f, _player->_view_angles[1] + (delta[1] * 0.022f));
    // No roll.
    _player->_view_angles[2] = 0.0f;

    _mouse_delta += delta;
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

#endif // CLIENT

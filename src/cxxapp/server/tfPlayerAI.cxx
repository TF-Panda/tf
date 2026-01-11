#ifdef SERVER

#include "../tfPlayer.h"
#include "datagramIterator.h"
#include "server.h"
#include "configVariableDouble.h"

ConfigVariableDouble sv_clock_correction_msecs
("sv-clock-correction-msecs", 60.0);

constexpr int max_cmd_backup = 64;

/**
 *
 */
float TFPlayer::
get_time_base() const {
  return _tick_base * GameServer::ptr()->get_tick_interval();
}

/**
 *
 */
CommandContext *TFPlayer::
alloc_command_context() {
  _command_contexts.push_back(CommandContext());
  return &_command_contexts.back();
}

/**
 *
 */
CommandContext *TFPlayer::
get_command_context(int i) {
  nassertr(i >= 0 && i < (int)_command_contexts.size(), nullptr);
  return &_command_contexts[i];
}

/**
 *
 */
void TFPlayer::
remove_command_context(int i) {
  _command_contexts.erase(_command_contexts.begin() + i);
}

/**
 *
 */
void TFPlayer::
remove_all_command_contexts() {
  _command_contexts.clear();
}

/**
 *
 */
CommandContext *TFPlayer::
remove_all_command_contexts_except_newest() {
  for (int i = (int)_command_contexts.size() - 2; i >= 0; --i) {
    _command_contexts.erase(_command_contexts.begin() + i);
  }
  assert(_command_contexts.size() == 1);
  return &_command_contexts.back();
}

/**
 *
 */
void TFPlayer::
replace_context_commands(CommandContext *ctx, PTA_PlayerCommand cmds, int count) {
  ctx->total_cmds = count;
  ctx->new_cmds = count;
  ctx->cmds = cmds;
}

/**
 *
 */
void TFPlayer::
process_player_commands(PTA_PlayerCommand cmds, int num_new_commands, bool paused) {
  CommandContext *ctx = alloc_command_context();

  ctx->total_cmds = (int)cmds.size();
  ctx->new_cmds = num_new_commands;
  ctx->cmds = cmds;
  ctx->paused = paused;

  if (ctx->paused) {
    for (int i = 0; i < ctx->total_cmds; ++i) {
      ctx->cmds[i].buttons = 0;
      ctx->cmds[i].move = 0.0f;
      ctx->cmds[i].view_angles = _view_angles;
    }
    ctx->dropped_packets = 0;
  }

  _paused = paused;
}

/**
 *
 */
int TFPlayer::
determine_simulation_ticks() {
  int ticks = 0;

  // Determine how much time we will be running this from and fixup
  // player clock as needed.
  for (size_t i = 0; i < _command_contexts.size(); ++i) {
    CommandContext *ctx = get_command_context(i);
    assert(ctx != nullptr);
    assert(ctx->new_cmds > 0);
    assert(ctx->dropped_packets >= 0);

    // Determine how long it will take to run those packets.
    ticks += ctx->new_cmds + ctx->dropped_packets;
  }

  return ticks;
}

/**
 *
 */
void TFPlayer::
adjust_player_time_base(int simulation_ticks) {
  assert(simulation_ticks >= 0);
  if (simulation_ticks < 0) {
    return;
  }

  GameServer *sv = GameServer::ptr();

  if (sv->get_max_clients()) {
    _tick_base = sv->get_tick_count() - simulation_ticks + sv->get_current_ticks_this_frame();

  } else {
    float correction_seconds = std::clamp((float)sv_clock_correction_msecs.get_value() / 100.0f, 0.0f, 1.0f);
    int correction_ticks = sv->time_to_ticks(correction_seconds);

    // Set the target tick correctionSeconds (rounded to ticks) ahead in
    // the future.  This way the client can alternate around this target
    // tick without getting smaller than base.sv.tickCount.  After
    // running the commands, simulation time should be equal or after
    // current base.sv.tickCount, otherwise the simulation time drops
    // out of the client side interpolated var history window.

    int ideal_final_tick = sv->get_tick_count() + correction_ticks;
    int estimated_final_tick = _tick_base + simulation_ticks;

    // If client gets ahead of this, we'll need to correct.
    int too_fast_limit = ideal_final_tick + correction_ticks;
    // If the client gets behind this, we'll also need to correct.
    int too_slow_limit = ideal_final_tick - correction_ticks;

    // See if we are too fast.
    if (estimated_final_tick > too_fast_limit || estimated_final_tick < too_slow_limit) {
      int corrected_tick = ideal_final_tick - simulation_ticks * sv->get_current_ticks_this_frame();
      _tick_base = corrected_tick;
    }
  }
}

/**
 * Task callback to simulate the player on the server.
 */
AsyncTask::DoneStatus TFPlayer::
simulate_task(GenericAsyncTask *task, void *data) {
  TFPlayer *player = (TFPlayer *)data;
  player->simulate();
  return AsyncTask::DS_cont;
}

/**
 *
 */
void TFPlayer::
simulate() {
  // Make sure not to simulate this guy twice per frame.
  GameServer *sv = GameServer::ptr();

  if (_simulation_tick == sv->get_tick_count()) {
    return;
  }

  _simulation_tick = sv->get_tick_count();

  // See how many PlayerCommands are queued up for running.
  int simulation_ticks = determine_simulation_ticks();

  // If some time will elapse, make sure our clock (_tick_base) starts
  // at the correct time.
  if (simulation_ticks > 0) {
    adjust_player_time_base(simulation_ticks);
  }

  size_t command_context_count = _command_contexts.size();

  // Build a list of available commands.
  PTA_PlayerCommand available_cmds;

  // Contexts go from oldest to newest.
  for (size_t i = 0; i < command_context_count; ++i) {
    CommandContext *ctx = get_command_context(i);
    if (ctx->cmds.empty()) {
      continue;
    }
    int num_backup = ctx->total_cmds - ctx->new_cmds;
    // If we haven't dropped too many packets, then run some commands.
    if (ctx->dropped_packets < 24) {
      int dropped_cmds = ctx->dropped_packets;

      // Run the last known cmd for each dropped cmd we don't have a backup for.
      while (dropped_cmds > num_backup) {
	++_last_cmd.tick_count;
	available_cmds.push_back(_last_cmd);
	--dropped_cmds;
      }

      // Now run the "history" commands if we still have dropped packets.
      while (dropped_cmds > 0) {
	int cmd_num = ctx->new_cmds + dropped_cmds - 1;
	available_cmds.push_back(ctx->cmds[cmd_num]);
	--dropped_cmds;
      }
    }

    // Now run any new commands.  Most recent command is at index 0.
    for (int i = ctx->new_cmds - 1; i >= 0; --i) {
      available_cmds.push_back(ctx->cmds[i]);
    }

    // Save off the last good command in case we drop > numbackup packets
    // and need to rerun them.  We'll use this to "guess" at what was in
    // the missing packets.
    _last_cmd = ctx->cmds[0];
  }

  // hs->sim_ticks_this_from == number of ticks remaining to be run, so we
  // should take the last N CUserCmds and postpone them until the next frame

  // If we're running multiple ticks this frame, don't peel off all of the
  // commands, spread them out over the server ticks. Use blocks of two in
  // alternate ticks
  int cmd_limit = 1;
  int cmds_to_run = (int)available_cmds.size();
  if (sv->get_current_ticks_this_frame() >= cmd_limit &&
      cmds_to_run > cmd_limit) {
    int cmds_to_roll_over = std::min(cmds_to_run, sv->get_current_ticks_this_frame() - 1);
    cmds_to_run = (int)available_cmds.size() - cmds_to_roll_over;
    assert(cmds_to_run >= 0);

    // Clear all contexts except last one.
    if (cmds_to_roll_over > 0) {
      CommandContext *ctx = remove_all_command_contexts_except_newest();
      replace_context_commands(ctx, available_cmds, cmds_to_roll_over);
    } else {
      // Clear all contexts.
      remove_all_command_contexts();
    }
  } else {
    // Clear all contexts.
    remove_all_command_contexts();
  }

  // Now run the commands.
  for (int i = 0; i < cmds_to_run; ++i) {
    run_player_command(&available_cmds[i], sv->get_delta_time());
  }
}

/**
 *
 */
void TFPlayer::
handle_player_command(const PlayerCommandArgs &args) {
  GameServer *sv = GameServer::ptr();
  ClientConnection *client = sv->get_client_sender();


  DatagramIterator scan(args.data);

  if (_last_movement_tick == sv->get_tick_count()) {
    return;
  }

  _last_movement_tick = sv->get_tick_count();

  int total_commands = args.num_backup_commands + args.num_new_commands;

  nassertv(args.num_new_commands >= 0);
  nassertv((total_commands - args.num_new_commands) >= 0);

  if (total_commands < 0 || total_commands >= (max_cmd_backup - 1)) {
    std::cerr << "Too many cmds (" << total_commands << ") sent to us from client " << client->id << "\n";
    return;
  }

  PlayerCommand null_cmd;
  PTA_PlayerCommand cmds;
  cmds.resize(total_commands);
  PlayerCommand *from, *to;

  from = &null_cmd;
  for (int i = total_commands - 1; i >= 0; --i) {
    to = &cmds[i];
    // Use prev as baseline.
    *to = *from;
    to->read(scan, *from);
    from = to;
  }

  process_player_commands(cmds, args.num_new_commands, false);
}

/**
 *
 */
void TFPlayer::
run_player_command(PlayerCommand *cmd, float dt) {
  _current_command = cmd;

  GameServer *sv = GameServer::ptr();
  sv->enter_simulation_time(cmd->tick_count, _tick_base);

  if (!is_dead()) {
    _view_angles = cmd->view_angles;

    // Factor just yaw into move direction.
    LQuaternionf view_angle_quat;
    view_angle_quat.set_hpr(LVecBase3f(cmd->view_angles[0], 0.0f, 0.0f));
    LVector3f view_forward = view_angle_quat.get_forward();
    LVector3f view_right = view_angle_quat.get_right();
    LVector3f world_move = view_forward * cmd->move[1] + view_right * cmd->move[0];

    set_pos(get_pos() + world_move * dt);
    LVecBase3f hpr = get_hpr();
    set_hpr(LVecBase3f(_view_angles[0], hpr[1], hpr[2]));
  }

  // Let time pass.
  ++_tick_base;

  // Store off the command number of this command so we can inform the client
  // that we ran it.
  _last_run_command_number = std::max(_last_run_command_number, (int)cmd->command_number);

  _current_command = nullptr;

  sv->exit_simulation_time();
}

/**
 * Returns the command number that we most recently executed for the player.
 */
int TFPlayer::
get_last_run_command_number() const {
  return _last_run_command_number;
}

#endif // SERVER

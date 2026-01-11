#ifdef CLIENT

#ifndef LOCALTFPLAYER_H
#define LOCALTFPLAYER_H

#include "referenceCount.h"
#include "../playerCommand.h"

class TFPlayer;

/**
 * Local player specific stuff for a TF player.
 */
class LocalTFPlayer : public ReferenceCount {
public:
  struct CommandContext {
    bool needs_processing = false;
    PlayerCommand *cmd = nullptr;
    int command_num = 0;
  };

  static constexpr int max_commands = 90;
  static constexpr int num_new_cmd_bits = 4;
  static constexpr int max_new_commands = ((1 << num_new_cmd_bits) - 1);
  static constexpr int num_backup_cmd_bits = 4;
  static constexpr int max_backup_commands = ((1 << num_backup_cmd_bits) - 1);

  static constexpr float base_move_speed = 300.0f;

  LocalTFPlayer(TFPlayer *player);

  void run_controls();
  void sample_mouse();

  void enable_controls();
  void disable_controls();

  PlayerCommand *get_next_command();
  int get_next_command_number() const;
  bool should_send_command() const;
  PlayerCommand *get_command(int num);
  void consider_send_command();
  void send_command();
  bool write_command_delta(Datagram &dg, int prev, int to, bool is_new);

  void calc_view();

  void simulate();
  void predict_command(PlayerCommand *cmd);

  void note_prediction_error(const LVector3f &delta);
  LVector3f get_prediction_error_smoothing_vector() const;

  inline void set_final_predicted_tick(int tick);
  inline int get_final_predicted_tick() const;

  inline int get_last_outgoing_command() const;
  inline int get_num_choked_commands() const;

  inline CommandContext *get_command_context();

  inline TFPlayer *get_player() const;

private:
  TFPlayer *_player;

  int _commands_sent;
  int _last_outgoing_command;
  int _choked_commands;
  float _next_command_time;
  PlayerCommand _last_command;
  PlayerCommand *_current_command;
  PlayerCommand _commands[max_commands];
  CommandContext _cmd_ctx;

  int _final_predicted_tick;
  float _prediction_error_time;
  LVector3f _prediction_error;

  LVecBase2f _last_mouse_sample;
  LVecBase2f _mouse_delta;

  bool _controls_enabled;
};

/**
 *
 */
inline void LocalTFPlayer::
set_final_predicted_tick(int tick) {
  _final_predicted_tick = tick;
}

/**
 *
 */
inline int LocalTFPlayer::
get_final_predicted_tick() const {
  return _final_predicted_tick;
}

/**
 *
 */
inline LocalTFPlayer::CommandContext *LocalTFPlayer::
get_command_context() {
  return &_cmd_ctx;
}

/**
 *
 */
inline TFPlayer *LocalTFPlayer::
get_player() const {
  return _player;
}

/**
 *
 */
inline int LocalTFPlayer::
get_last_outgoing_command() const {
  return _last_outgoing_command;
}

/**
 *
 */
inline int LocalTFPlayer::
get_num_choked_commands() const {
  return _choked_commands;
}

#endif // LOCALTFPLAYER_H

#endif // CLIENT

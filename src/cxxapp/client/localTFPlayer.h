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

private:
  TFPlayer *_player;

  int _commands_sent;
  int _last_outgoing_command;
  int _command_ack;
  int _last_command_ack;
  int _choked_commands;
  float _next_command_time;
  PlayerCommand _last_command;
  PlayerCommand *_current_command;
  PlayerCommand _commands[max_commands];

  int _final_predicted_tick;

  LVecBase2f _last_mouse_sample;
  LVecBase2f _mouse_delta;

  LVecBase3f _prediction_error;
  float _prediction_error_time;

  bool _controls_enabled;
};

#endif // LOCALTFPLAYER_H

#endif // CLIENT

#ifndef TFPLAYER_H
#define TFPLAYER_H

#include "entity.h"
#include "playerCommand.h"
#include "pointerToArray.h"
#include "notifyCategoryProxy.h"

NotifyCategoryDeclNoExport(tfplayer);

class LocalTFPlayer;

#ifdef SERVER
/**
 *
 */
struct CommandContext {
  PTA_PlayerCommand cmds;
  int new_cmds = 0;
  int total_cmds = 0;
  int dropped_packets = 0;
  bool paused = false;
};
#endif // SERVER

/**
 *
 */
class TFPlayer : public Entity {
public:
  TFPlayer();

  inline void set_player_name(const std::string &name);
  inline const std::string &get_player_name() const;

  virtual void pre_generate() override;
  virtual void generate() override;
  virtual void disable() override;

#ifdef CLIENT
  inline LocalTFPlayer *get_local_player() const;
#endif

#ifdef SERVER
  float get_time_base() const;
  void simulate();
#endif

private:
  static void s_recv_player_command(void *obj, void *pargs);

#ifdef SERVER
  void handle_player_command(const PlayerCommandArgs &args);
  void process_player_commands(PTA_PlayerCommand cmds, int num_new_commands, bool paused);
  CommandContext *alloc_command_context();
  void remove_command_context(int i);
  void remove_all_command_contexts();
  CommandContext *remove_all_command_contexts_except_newest();
  void replace_context_commands(CommandContext *ctx, PTA_PlayerCommand cmds, int count);
  CommandContext *get_command_context(int i);
  int determine_simulation_ticks();
  void adjust_player_time_base(int simulation_ticks);
  void run_player_command(PlayerCommand *cmd, float dt);
#endif

private:
  std::string _player_name;
  LVecBase3f _view_angles;
  unsigned int _tick_base;

#ifdef CLIENT
  PT(LocalTFPlayer) _local_player;
#endif

#ifdef SERVER
  int _last_movement_tick;
  int _simulation_tick;
  bool _paused;
  PlayerCommand *_current_command;
  PlayerCommand _last_cmd;
  int _last_run_command_number;
  pvector<CommandContext> _command_contexts;
#endif // SERVER

public:
  static NetworkObject *make_TFPlayer() {
    return new TFPlayer;
  }
  virtual NetworkClass *get_network_class() const override {
    return _network_class;
  }
  inline static NetworkClass *get_type_network_class() {
    return _network_class;
  }
  static void init_network_class();
private:
  static NetworkClass *_network_class;

  friend class LocalTFPlayer;
};

/**
 *
 */
inline void TFPlayer::
set_player_name(const std::string &name) {
  _player_name = name;
}

/**
 *
 */
inline const std::string &TFPlayer::
get_player_name() const {
  return _player_name;
}

#ifdef CLIENT

/**
 *
 */
inline LocalTFPlayer *TFPlayer::
get_local_player() const {
  return _local_player;
}

#endif // CLIENT

#endif // TFPLAYER_H

#ifndef TFPLAYER_H
#define TFPLAYER_H

#include "entity.h"
#include "playerCommand.h"
#include "pointerToArray.h"
#include "notifyCategoryProxy.h"
#include "gameEnums.h"

NotifyCategoryDeclNoExport(tfplayer);

class LocalTFPlayer;
class Weapon;

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
  static constexpr int max_weapons = 6;

  TFPlayer();

  static std::string get_tf_class_model(TFClass cls);

  inline void set_player_name(const std::string &name);
  inline const std::string &get_player_name() const;

  // Weapon list stuff.
  inline int get_num_weapons() const;
  inline DO_ID get_weapon_do_id(int n) const;
  Weapon *get_weapon(int n) const;
  inline int get_active_weapon_index() const;
  inline bool has_active_weapon() const;
  Weapon *get_active_weapon() const;

  inline TFClass get_tf_class() const;

  virtual void pre_generate() override;
  virtual void generate() override;
  virtual void disable() override;

  inline unsigned int get_tick_base() const;

  virtual void simulate() override;

#ifdef CLIENT
  virtual bool should_predict() const override;
  virtual void add_prediction_fields() override;
  inline LocalTFPlayer *get_local_player() const;
#endif

#ifdef SERVER
  float get_time_base() const;
  int get_last_run_command_number() const;
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

  static AsyncTask::DoneStatus simulate_task(GenericAsyncTask *task, void *data);
#endif

private:
  std::string _player_name;
  LVecBase3f _view_angles;
  unsigned int _tick_base;
  TFClass _tf_class;

  // Movement state stuff.
  bool _on_ground;
  bool _ducked;
  bool _ducking;
  bool _in_duck_jump;
  bool _duck_flag;
  float _duck_time;
  float _duck_jump_time;
  float _jump_time;

  // For engineers, how much metal do we have?
  int _metal;

  float _eye_pitch;
  float _eye_yaw;

  DO_ID _weapon_ids[max_weapons];
  int _num_weapons;
  int _active_weapon;

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
 * Returns the number of weapons the player has.
 */
inline int TFPlayer::
get_num_weapons() const {
  return _num_weapons;
}

/**
 * Returns the doId of the player's Nth weapon.
 */
inline DO_ID TFPlayer::
get_weapon_do_id(int n) const {
  nassertr(n >= 0 && n < _num_weapons, 0);
  return _weapon_ids[n];
}

/**
 * Returns the index into _weapon_ids of the player's currently active weapon.
 */
inline int TFPlayer::
get_active_weapon_index() const {
  return _active_weapon;
}

/**
 *
 */
inline bool TFPlayer::
has_active_weapon() const {
  return _active_weapon >= 0 && _active_weapon < _num_weapons;
}

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

/**
 *
 */
inline TFClass TFPlayer::
get_tf_class() const {
  return (TFClass)_tf_class;
}

/**
 *
 */
inline unsigned int TFPlayer::
get_tick_base() const {
  return _tick_base;
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

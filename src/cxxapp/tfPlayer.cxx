#include "tfPlayer.h"
#include "networkClass.h"
#include "modelPool.h"
#include "textNode.h"
#include "gameGlobals.h"
#include "loader.h"
#include "playerCommand.h"
#include "vectorNetClasses.h"
#ifdef CLIENT
#include "client/localTFPlayer.h"
#endif

NotifyCategoryDef(tfplayer, "tf");

NetworkClass *TFPlayer::_network_class = nullptr;

/**
 *
 */
TFPlayer::
TFPlayer() :
  Entity("tfplayer"),
  _tick_base(0u),
  _view_angles(0.0f),
  _tf_class(TFCLASS_engineer),
  _metal(100),
  _on_ground(true),
  _ducked(false),
  _ducking(false),
  _in_duck_jump(false),
  _duck_time(0.0f),
  _duck_jump_time(0.0f),
  _eye_pitch(0.0f),
  _eye_yaw(0.0f),
  _active_weapon(-1),
  _num_weapons(0)
#ifdef SERVER
  ,
  _last_movement_tick(-1),
  _simulation_tick(0),
  _paused(false),
  _current_command(nullptr),
  _last_run_command_number(0)
#endif
#ifdef CLIENT
  ,
  _local_player(nullptr)
#endif
{
  // Default the weapon IDs to null doIds.
  for (int i = 0; i < max_weapons; ++i) {
    _weapon_ids[i] = 0;
  }
}

/**
 *
 */
void TFPlayer::
pre_generate() {
  NetworkObject::pre_generate();
#ifdef CLIENT
  if (is_owner()) {
    assert(globals.local_avatar == nullptr);
    globals.local_avatar = this;
    _local_player = new LocalTFPlayer(this);
  }
#endif
#ifdef SERVER
  _tf_class = TFCLASS_soldier;
#endif
}

/**
 *
 */
void TFPlayer::
generate() {
  Entity::generate();

#ifdef CLIENT
  Loader *loader = Loader::get_global_ptr();
  PT(PandaNode) mdl = loader->load_sync(get_tf_class_model((TFClass)_tf_class));
  NodePath mdl_path(mdl);
  mdl_path.reparent_to(_node_path);

  // Also put some text showing their player name.
  PT(TextNode) name_text = new TextNode("player-name-text");
  name_text->set_text(_player_name);
  name_text->set_align(TextNode::A_center);
  NodePath text_path(name_text->generate());
  text_path.set_pos(0.0f, 0.0f, 100.0f);
  text_path.set_scale(3.0f);
  text_path.set_billboard_point_eye();
  text_path.reparent_to(_node_path);
#endif

#ifdef SERVER
  // Spawn a task to simulate the player.
  add_sim_task("simulate", simulate_task);
#endif
}

/**
 *
 */
void TFPlayer::
disable() {
#ifdef CLIENT
  if (is_owner()) {
    assert(globals.local_avatar == this);
    globals.local_avatar = nullptr;
    _local_player = nullptr;
  }
#endif
  Entity::disable();
}

#ifdef CLIENT
/**
 * This will only be called on the client when simulating the local player.
 * The server simulation is defined in tfPlayerAI.cxx.
 */
void TFPlayer::
simulate() {
  if (_local_player != nullptr) {
    // Just pass it onto the local player.
    _local_player->simulate();
  }
}

/**
 * Returns true if we should predict this entity.  We predict the local player.
 */
bool TFPlayer::
should_predict() const {
  return _is_owner && _local_player != nullptr;
}

/**
 *
 */
void TFPlayer::
add_prediction_fields() {
  Entity::add_prediction_fields();
  add_pred_field("tick_base", &_tick_base);
}
#endif

/**
 * Returns the Weapon instance for the player's nth weapon.
 */
Weapon *TFPlayer::
get_weapon(int n) const {
  nassertr(n >= 0 && n < _num_weapons, nullptr);
  return (Weapon *)globals.get_do_by_id(_weapon_ids[n]);
}

/**
 * Returns the Weapon instance for the player's active weapon, or nullptr
 * if the player has no weapon active right now.
 */
Weapon *TFPlayer::
get_active_weapon() const {
  if (_active_weapon >= 0 && _active_weapon < _num_weapons) {
    return get_weapon(_active_weapon);
  } else {
    return nullptr;
  }
}

/**
 *
 */
void TFPlayer::
s_recv_player_command(void *obj, void *pargs) {
#ifdef SERVER
  TFPlayer *player = (TFPlayer *)obj;
  PlayerCommandArgs *args = (PlayerCommandArgs *)pargs;
  player->handle_player_command(*args);
#endif
}

/**
 *
 */
void TFPlayer::
init_network_class() {
  PlayerCommandArgs::init_network_class();
  PlayerCommand::init_type();
  BEGIN_NETWORK_CLASS(TFPlayer, Entity);
  _network_class->set_factory_func(make_TFPlayer);
  MAKE_NET_FIELD(TFPlayer, _player_name, NetworkField::DT_string);
  MAKE_NET_FIELD(TFPlayer, _tf_class, NetworkField::DT_uint8);
  MAKE_NET_FIELD(TFPlayer, _on_ground, NetworkField::DT_bool);
  MAKE_NET_FIELD(TFPlayer, _ducked, NetworkField::DT_bool);
  MAKE_NET_FIELD(TFPlayer, _ducking, NetworkField::DT_bool);
  MAKE_NET_FIELD(TFPlayer, _in_duck_jump, NetworkField::DT_bool);
  MAKE_NET_FIELD(TFPlayer, _duck_flag, NetworkField::DT_bool);
  MAKE_NET_FIELD(TFPlayer, _duck_time, NetworkField::DT_float);
  MAKE_NET_FIELD(TFPlayer, _duck_jump_time, NetworkField::DT_float);
  MAKE_NET_FIELD(TFPlayer, _metal, NetworkField::DT_int16);
  MAKE_NET_FIELD(TFPlayer, _eye_pitch, NetworkField::DT_float);
  MAKE_NET_FIELD(TFPlayer, _eye_yaw, NetworkField::DT_float);
  MAKE_NET_FIELD(TFPlayer, _tick_base, NetworkField::DT_uint32);
  MAKE_NET_FIELD(TFPlayer, _num_weapons, NetworkField::DT_uint8);
  MAKE_NET_FIELD(TFPlayer, _active_weapon, NetworkField::DT_int8);
  MAKE_NET_FIELD(TFPlayer, _weapon_ids, NetworkField::DT_uint32);
  MAKE_NET_RPC(player_command, PlayerCommandArgs::get_network_class(), NetworkRPC::F_ownsend, s_recv_player_command);
  END_NETWORK_CLASS();
}

/**
 * Returns the model to use for a TF class.
 */
std::string TFPlayer::
get_tf_class_model(TFClass cls) {
  switch (cls) {
  case TFCLASS_scout:
    return "models/char/scout";
  case TFCLASS_soldier:
    return "models/char/soldier";
  case TFCLASS_pyro:
    return "models/char/pyro";
  case TFCLASS_demoman:
    return "models/char/demo";
  case TFCLASS_hwguy:
    return "models/char/heavy";
  case TFCLASS_engineer:
    return "models/char/engineer";
  case TFCLASS_sniper:
    return "models/char/sniper";
  case TFCLASS_medic:
    return "models/char/medic";
  case TFCLASS_spy:
    return "models/char/spy";
  default:
    return "models/char/scout";
  }
}

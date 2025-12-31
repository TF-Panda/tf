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
  _view_angles(0.0f)
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
}

/**
 *
 */
void TFPlayer::
generate() {
  Entity::generate();

#ifdef CLIENT
  // Temp model to represent player.  lol.
  Loader *loader = Loader::get_global_ptr();
  PT(PandaNode) mdl = loader->load_sync("models/misc/smiley");
  NodePath mdl_path(mdl);
  mdl_path.set_scale(16.0f);
  mdl_path.reparent_to(_node_path);

  // Also put some text showing their player name.
  PT(TextNode) name_text = new TextNode("player-name-text");
  name_text->set_text(_player_name);
  name_text->set_align(TextNode::A_center);
  NodePath text_path(name_text->generate());
  text_path.set_pos(0.0f, 0.0f, 20.0f);
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
  // View angles aren't networked, only sent from client to server in commands.
  // Only server and local player know their view angles.
  //MAKE_STRUCT_NET_FIELD(TFPlayer, _view_angles, Angles_NetClass::get_network_class());
  MAKE_NET_FIELD(TFPlayer, _tick_base, NetworkField::DT_uint32);
  MAKE_NET_RPC(player_command, PlayerCommandArgs::get_network_class(), NetworkRPC::F_ownsend, s_recv_player_command);
  END_NETWORK_CLASS();
}

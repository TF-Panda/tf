#include "gameManager.h"
#include "networkClass.h"
#include "networkObject.h"
#include "notifyCategoryProxy.h"

#ifdef SERVER
#include "server/server.h"
#include "tfPlayer.h"
#endif
#ifdef CLIENT
#include "client/client.h"
#endif

NotifyCategoryDeclNoExport(gamemanager);
NotifyCategoryDef(gamemanager, "tf");

NetworkClass *GameManager::_network_class = nullptr;

struct JoinGameArgs {
  std::string player_name;

  static NetworkClass *get_network_class() {
    return _network_class;
  }
  static void init_network_class() {
    BEGIN_NETWORK_CLASS_NOBASE(JoinGameArgs);
    MAKE_NET_FIELD(JoinGameArgs, player_name, NetworkField::DT_string);
    END_NETWORK_CLASS();
  }
private:
  static NetworkClass *_network_class;
};
NetworkClass *JoinGameArgs::_network_class = nullptr;

struct JoinGameRespArgs {
  int tick_count;

  static NetworkClass *get_network_class() {
    return _network_class;
  }
  static void init_network_class() {
    BEGIN_NETWORK_CLASS_NOBASE(JoinGameRespArgs);
    MAKE_NET_FIELD(JoinGameRespArgs, tick_count, NetworkField::DT_uint32);
    END_NETWORK_CLASS();
  }
private:
  static NetworkClass *_network_class;
};
NetworkClass *JoinGameRespArgs::_network_class = nullptr;

/**
 *
 */
void GameManager::
s_recv_join_game(void *obj, void *pargs) {
#ifdef SERVER
  GameServer *server = GameServer::ptr();
  ClientConnection *client = server->get_client_sender();
  GameManager *mgr = (GameManager *)obj;
  JoinGameArgs *args = (JoinGameArgs *)pargs;
  gamemanager_cat.info()
    << "Got join game from client " << client->id << ", player name is " << args->player_name << "\n";

  // Make their player entity and mark them as the owner.
  // This will implicitly give the client interest into the
  // game zone, which we've assigned the player entity to.
  PT(TFPlayer) player = new TFPlayer;
  player->set_player_name(args->player_name);
  server->generate_object(player, game_zone, client);

  JoinGameRespArgs resp_args;
  resp_args.tick_count = server->get_tick_count();
  server->send_obj_message(mgr, "join_game_resp", &resp_args, client);
#endif
}

/**
 *
 */
void GameManager::
s_recv_join_game_resp(void *obj, void *pargs) {
#ifdef CLIENT
  GameManager *mgr = (GameManager *)obj;
  JoinGameRespArgs *args = (JoinGameRespArgs *)pargs;
  GameClient::ptr()->reset_simulation(args->tick_count);
  gamemanager_cat.info()
    << "Got join game response, reset simulation to tick " << args->tick_count << "\n";
#endif
}

/**
 *
 */
void GameManager::
generate() {
  NetworkObject::generate();
#ifdef CLIENT
  gamemanager_cat.info()
    << "Game manager generated! Zone ID " << get_zone_id() << ", do id " << get_do_id() << "\n";
  gamemanager_cat.info()
    << "Level name is: " << _level_name << "\n";
  JoinGameArgs args;
  args.player_name = "bribri25";
  GameClient::ptr()->send_obj_message(this, "join_game", &args);
#endif
}

/**
 *
 */
void GameManager::
init_network_class() {
  JoinGameArgs::init_network_class();
  JoinGameRespArgs::init_network_class();

  BEGIN_NETWORK_CLASS_NOBASE(GameManager);
  _network_class->set_factory_func(make_GameManager);
  MAKE_NET_FIELD(GameManager, _game_name, NetworkField::DT_string);
  MAKE_NET_FIELD(GameManager, _level_name, NetworkField::DT_string);
  MAKE_NET_RPC(join_game, JoinGameArgs::get_network_class(), NetworkRPC::F_clsend, s_recv_join_game);
  MAKE_NET_RPC(join_game_resp, JoinGameRespArgs::get_network_class(), NetworkRPC::F_none, s_recv_join_game_resp);
  END_NETWORK_CLASS();
}

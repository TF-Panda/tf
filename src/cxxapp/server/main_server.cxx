#include "clockObject.h"
#ifdef SERVER

#include "server.h"
#include "configVariableInt.h"
#include "configVariableString.h"
#include "../networkClasses.h"
#include "../gameManager.h"
#include "../gameGlobals.h"

ConfigVariableInt sv_port("sv-port", "27015", PRC_DESC("Server port to talk over."));
ConfigVariableString tf_map("tf-map", "", PRC_DESC("Level to load."));

/**
 * Server entry point.
 */
int
main(int argc, char *argv[]) {
  init_network_classes();

  globals.render = NodePath("render");

  GameServer *sv = GameServer::ptr();

  globals.simbase = sv;
  globals.sv = sv;

  sv->startup(sv_port);

  PT(GameManager) game_mgr = new GameManager;
  game_mgr->set_level_name(tf_map);
  sv->generate_object(game_mgr, game_manager_zone);
  globals.game = game_mgr;

  ClockObject *clock = ClockObject::get_global_clock();

  while (true) {
    clock->tick();
    sv->run_frame();
  }

  return 0;
}

#endif // SERVER

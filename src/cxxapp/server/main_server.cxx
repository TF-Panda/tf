#ifdef SERVER

#include "server.h"
#include "configVariableInt.h"
#include "configVariableString.h"
#include "../networkClasses.h"
#include "../gameManager.h"
#include "../gameGlobals.h"
#include "asyncTaskManager.h"
#include "config_anim.h"
#include "clockObject.h"
#include "physSystem.h"
#include "physScene.h"

ConfigVariableInt sv_port("sv-port", "27015", PRC_DESC("Server port to talk over."));
ConfigVariableString tf_map("tf-map", "levels/ctf_2fort", PRC_DESC("Level to load."));

/**
 * Server entry point.
 */
int
main(int argc, char *argv[]) {
  init_libanim();

  init_network_classes();

  globals.render = NodePath("render");
  globals.dyn_render = globals.render.attach_new_node("dynamic_render");

  // Initialize physics.
  // TODO: move physics stuff into a manager class?
  PhysSystem *phys = PhysSystem::ptr();
  if (!phys->initialize()) {
    std::cerr << "Failed to initialize PhysX!\n";
    return 1;
  }
  PT(PhysScene) phys_world = new PhysScene;
  phys_world->set_gravity(LVector3f(0, 0, -800.0f));
  phys_world->set_fixed_timestep(0.015f);
  globals.physics_world = phys_world;

  GameServer *sv = GameServer::ptr();

  globals.simbase = sv;
  globals.sv = sv;
  globals.task_mgr = AsyncTaskManager::get_global_ptr();
  PT(AsyncTaskManager) sim_task_mgr = new AsyncTaskManager("simulation");
  globals.sim_task_mgr = sim_task_mgr;

  sv->startup(sv_port);

  PT(GameManager) game_mgr = new GameManager;
  sv->generate_object(game_mgr, game_manager_zone);
  // Load the level.
  game_mgr->change_level(tf_map.get_value());

  ClockObject *clock = ClockObject::get_global_clock();

  while (true) {
    clock->tick();
    sv->run_frame();
    phys_world->simulate(clock->get_dt());
  }

  return 0;
}

#endif // SERVER

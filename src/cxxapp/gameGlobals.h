#ifndef GAMEGLOBALS_H
#define GAMEGLOBALS_H

#include "nodePath.h"
#include "gameEnums.h"
#include "networkObject.h"

class SimulationManager;
class AsyncTaskManager;

#ifdef CLIENT
#include "pointerTo.h"
#include "lens.h"
#include "camera.h"
class GameClient;
class GraphicsStateGuardian;
class GraphicsWindow;
class GraphicsPipe;
class InputManager;
class LocalTFPlayer;
#endif

#ifdef SERVER
class GameServer;
#endif

class GameManager;
class TFPlayer;

class PhysScene;

/**
 * Holds various global variables.
 */
struct GameGlobals {
  NodePath render;
  // Scene root for stuff that is culled against the map's PVS.
  NodePath dyn_render;
  SimulationManager *simbase = nullptr;
  GameManager *game = nullptr;

  PhysScene *physics_world;

  // For tasks that run per rendering frame.
  AsyncTaskManager *task_mgr = nullptr;
  // For tasks that run on simulation ticks.
  AsyncTaskManager *sim_task_mgr = nullptr;

  // Client-specific globals.
#ifdef CLIENT
  NodePath camera;
  PT(Camera) camera_node = nullptr;
  PT(Lens) camera_lens = nullptr;
  GameClient *cr = nullptr;
  TFPlayer *local_avatar = nullptr;
  GraphicsStateGuardian *gsg = nullptr;
  GraphicsWindow *win = nullptr;
  GraphicsPipe *pipe = nullptr;
  InputManager *input = nullptr;
  LocalTFPlayer *get_local_tf_player() const;
#endif
#ifdef SERVER
  GameServer *sv = nullptr;
#endif

  NetworkObject *get_do_by_id(DO_ID do_id) const;
};

extern GameGlobals globals;

#endif // GAMEGLOBALS_H

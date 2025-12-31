#ifndef GAMEGLOBALS_H
#define GAMEGLOBALS_H

#include "nodePath.h"

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

/**
 * Holds various global variables.
 */
struct GameGlobals {
  NodePath render;
  SimulationManager *simbase = nullptr;
  GameManager *game = nullptr;

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
};

enum EntityParentCode {
  EPC_unchanged = -1,
  EPC_render = -2,
  EPC_hidden = -3,
  EPC_viewmodel = -4,
  EPC_viemwodel_camera = -5,
  EPC_camera = -6,
  EPC_dyn_render = -7,
  EPC_skybox = -8,
};

enum TFTeam {
  TFTEAM_no_team,
  TFTEAM_spectate,
  TFTEAM_red,
  TFTEAM_blue,
};

enum InputCommand {
  IC_primary_attack = 1 << 0,
  IC_secondary_attack = 1 << 1,
  IC_move_forward = 1 << 2,
  IC_move_back = 1 << 3,
  IC_move_left = 1 << 4,
  IC_move_right = 1 << 5,
  IC_jump = 1 << 6,
  IC_duck = 1 << 7,
  IC_reload = 1 << 8,
  IC_walk = 1 << 9,
  IC_sprint = 1 << 10,
  IC_interact = 1 << 11,
  IC_pause = 1 << 12,
  IC_axis_move_x = 1 << 13,
  IC_axis_move_y = 1 << 14,
  IC_axis_look_x = 1 << 15,
  IC_axis_look_y = 1 << 16,
};

extern GameGlobals globals;

#endif // GAMEGLOBALS_H

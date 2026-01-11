#ifdef CLIENT

#include "inputButtons.h"
#include "perspectiveLens.h"
#include "client.h"
#include "frameBufferProperties.h"
#include "windowProperties.h"
#include "graphicsEngine.h"
#include "graphicsPipeSelection.h"
#include "graphicsPipe.h"
#include "graphicsWindow.h"
#include "frameRateMeter.h"
#include "configVariableBool.h"
#include "configVariableDouble.h"
#include "config_shader.h"
#include "../networkClasses.h"
#include "../gameGlobals.h"
#include "inputManager.h"
#include "localTFPlayer.h"
#include "../tfPlayer.h"
#include "asyncTaskManager.h"
#include "config_anim.h"
#include "sounds.h"
#include "dynamicVisNode.h"
#include "physScene.h"
#include "physSystem.h"

ConfigVariableBool show_frame_rate_meter
("show-frame-rate-meter", false,
 PRC_DESC("Toggles showing a basic frame rate meter in the top right corner of the window."));

ConfigVariableDouble fov
("fov", 75.0,
 PRC_DESC("The field-of-view in degrees of the main camera lens."));

/**
 *
 */
void
sign_on_callback(GameClient *cl, bool success, const std::string &msg) {
  std::cerr << "Sign on callback: " << success << ", " << msg << "\n";
}

/**
 *
 */
void
connect_callback(GameClient *cl, bool success, const NetAddress &addr) {
  if (success) {
    std::cerr << "Connected to server at " << addr << "\n";
  } else {
    std::cerr << "Failed to connect to server at " << addr << "\n";
  }

  cl->send_hello(sign_on_callback);
}

/**
 *
 */
void
disconnect_callback(GameClient *cl) {
  std::cerr << "Disconnected from server!\n";
}

/**
 *
 */
void
adjust_aspect_ratio(LVecBase2i size, PerspectiveLens *lens) {
  float ratio = (float)size.get_x() / (float)size.get_y();
  lens->set_aspect_ratio(ratio);
}

/**
 * Main entry point for client process.
 */
int
main(int argc, char *argv[]) {
  init_libshader();
  init_libanim();

  init_network_classes();

  //
  // Graphics/scene graph initialization.
  //
  GraphicsEngine *graphics_engine = GraphicsEngine::get_global_ptr();
  GraphicsPipeSelection *selection = GraphicsPipeSelection::get_global_ptr();
  PT(GraphicsPipe) pipe = selection->make_default_pipe();

  WindowProperties win_props = WindowProperties::get_default();
  FrameBufferProperties fb_props = FrameBufferProperties::get_default();
  unsigned int window_flags = GraphicsPipe::BF_require_window | GraphicsPipe::BF_fb_props_optional;
  GraphicsOutput *output  = graphics_engine->make_output(pipe, "main-window", 0, fb_props, win_props, window_flags);
  if (output == nullptr) {
    std::cerr << "Failed to open main window!\n";
    return 1;
  }
  GraphicsStateGuardian *gsg = output->get_gsg();
  GraphicsWindow *window = DCAST(GraphicsWindow, output);

  NodePath render("render");
  globals.render = render;

  PT(DynamicVisNode) dyn_vis_node = new DynamicVisNode("dynamic_render");
  NodePath dyn_render = render.attach_new_node(dyn_vis_node);
  globals.dyn_render = dyn_render;

  PT(Camera) cam = new Camera("camera");
  PT(PerspectiveLens) lens = new PerspectiveLens;
  lens->set_aspect_ratio(4.0f / 3.0f);
  lens->set_min_fov(fov.get_value() / (4.0f / 3.0f));
  cam->set_lens(lens);
  NodePath cam_path = render.attach_new_node(cam);

  InputManager input;
  input.initialize(window, cam);
  //  input.enable_mouse();

  // Set up globals.
  globals.camera = cam_path;
  globals.camera_node = cam;
  globals.camera_lens = lens;
  globals.input = &input;
  globals.win = window;
  globals.gsg = gsg;
  globals.pipe = pipe;
  globals.task_mgr = AsyncTaskManager::get_global_ptr();
  PT(AsyncTaskManager) sim_task_mgr = new AsyncTaskManager("simulation");
  globals.sim_task_mgr = sim_task_mgr;

  PT(DisplayRegion) display_region = window->make_display_region();
  display_region->set_camera(cam_path);

  // Wait for window to fully realize on screen.
  graphics_engine->open_windows();

  PT(FrameRateMeter) fps_meter = nullptr;
  if (show_frame_rate_meter) {
    // We want a frame rate meter.
    fps_meter = new FrameRateMeter("frame-rate-meter");
    fps_meter->setup_window(window);
  }

  // Initialize audio.
  SoundManager *sound_mgr = SoundManager::ptr();
  sound_mgr->initialize();
  sound_mgr->load_sounds();
  //sound_mgr->list_sounds();

  // Initialize physics.
  PhysSystem *phys = PhysSystem::ptr();
  if (!phys->initialize()) {
    std::cerr << "Failed to initialize PhysX!\n";
    return 1;
  }
  PT(PhysScene) phys_world = new PhysScene;
  phys_world->set_gravity(LVector3f(0, 0, -800.0f));
  phys_world->set_fixed_timestep(0.015f);
  globals.physics_world = phys_world;

  PT(AudioSound) music = sound_mgr->get_music_manager()->get_sound("audio/bgm/gamestartup1.mp3");
  music->set_loop(true);
  music->play();

  // Connect to server.
  NetAddress server_addr;
  server_addr.set_host("127.0.0.1", 27015);

  GameClient *cl = GameClient::ptr();
  globals.simbase = cl;
  globals.cr = cl;

  cl->set_disconnect_callback(disconnect_callback);
  cl->try_connect(server_addr, connect_callback);

  LVecBase2i last_window_size = window->get_size();
  adjust_aspect_ratio(last_window_size, lens);

  ClockObject *clock = ClockObject::get_global_clock();

  // Main loop.
  while (!window->is_closed()) {
    LocalTFPlayer *local_player = globals.get_local_tf_player();

    input.update();

    if (local_player != nullptr) {
      local_player->sample_mouse();
    }

    if (input.was_button_pressed(IB_jump)) {
      sound_mgr->create_sound_by_name("Weapon_FlameThrower.AirBurstAttack")->play();
    }

    sound_mgr->update();

    cl->run_frame();

    cl->run_prediction();
    NetworkObject::interpolate_objects();

    // Run physics.
    phys_world->simulate(clock->get_dt());

    // If we have a local player, have them calculate our view (camera position and angles).
    if (local_player != nullptr) {
      local_player->calc_view();
    }

    // Update the dynamic vis node if any children moved.  They need their
    // PVS sector assignments updated.
    dyn_vis_node->update_dirty_children();

    // Update lens for new aspect ratio if window was resized.
    LVecBase2i window_size = window->get_size();
    if (window_size != last_window_size) {
      adjust_aspect_ratio(window_size, lens);
      last_window_size = window_size;
    }

    graphics_engine->render_frame();
  }

  std::cerr << "Main window closed, exiting.\n";

  return 0;
}

#endif

#ifdef CLIENT

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

  globals.render.ls();

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

  // Main loop.
  while (!window->is_closed()) {
    LocalTFPlayer *local_player = globals.get_local_tf_player();

    input.update();

    if (local_player != nullptr) {
      local_player->sample_mouse();
    }

    cl->run_frame();

    NetworkObject::interpolate_objects();

    // If we have a local player, have them calculate our view (camera position and angles).
    if (local_player != nullptr) {
      local_player->calc_view();
    }

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

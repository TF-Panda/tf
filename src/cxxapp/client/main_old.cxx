
#include "graphicsPipeSelection.h"
#include "graphicsEngine.h"
#include "load_prc_file.h"
#include "modelPool.h"
#include "pointerTo.h"
#include "player.h"
#include "loader.h"
#include "config_map.h"
#include "config_shader.h"
#include "configVariableInt.h"
#include "luse.h"
#include "inputManager.h"
#include "globals.h"
#include "clockObject.h"
#include "eventHandler.h"
#include "physScene.h"
#include "physSystem.h"
#include "characterNode.h"
#include "character.h"
#include "mapLightingEffect.h"
#include "mapRender.h"
#include "mapRoot.h"
#include "world.h"

NodePath scene_root;
PT(Player) player;
NodePath camera;
InputManager input;
NodePath toon;
PT(MapRender) map_render;
PT(World) world;
NodePath level_root;

bool mouse_move_on = false;

PT(PhysScene) physics_world;

static constexpr float walkspeed = 200.0f;
static constexpr float maxspeed = 200.0f;

void
load_level(const Filename &level) {
  PT(PandaNode) node = Loader::get_global_ptr()->load_sync(level);
  NodePath np(node);
  nassertv(node != nullptr);
  //scene_root.attach_new_node(node);
  MapData *mdata = DCAST(MapRoot, np.find("**/+MapRoot").node())->get_data();
  map_render->set_map_data(mdata);
  globals->map_data = mdata;
  level_root = np;
}

void
calc_view() {
  camera.set_pos(player->get_node_path().get_pos() + player->get_eye_offset());
  camera.set_hpr(player->get_view_angles());
}

void
start_mouse_movement() {
  WindowProperties props;
  props.set_cursor_hidden(true);
  props.set_mouse_mode(WindowProperties::M_relative);
  globals->win->request_properties(props);
}

void
stop_mouse_movement() {
  WindowProperties props;
  props.set_cursor_hidden(false);
  props.set_mouse_mode(WindowProperties::M_absolute);
  globals->win->request_properties(props);
}

void
toggle_mouse() {
  mouse_move_on = !mouse_move_on;
  if (mouse_move_on) {
    start_mouse_movement();
  } else {
    stop_mouse_movement();
  }
}

int
main(int argc, char *argv[]) {
  init_libmap();
  init_libshader();

  Entity::init_type();
  Player::init_type();
  World::init_type();
  World::register_ent_factory();

  Loader *loader = Loader::get_global_ptr();

  GraphicsPipeSelection *selection = GraphicsPipeSelection::get_global_ptr();
  PT(GraphicsPipe) pipe = selection->make_default_pipe();
  GraphicsEngine *engine = GraphicsEngine::get_global_ptr();
  WindowProperties props = WindowProperties::get_default();
  props.set_raw_mice(true);
  GraphicsOutput *output = engine->make_output(pipe, "main-window", 0, FrameBufferProperties::get_default(), props, GraphicsPipe::BF_require_window | GraphicsPipe::BF_fb_props_optional);
  PT(GraphicsWindow) window = DCAST(GraphicsWindow, output);
  PT(DisplayRegion) region = window->make_display_region();
  map_render = new MapRender("map");
  scene_root = NodePath(map_render);
  PT(PerspectiveLens) lens = new PerspectiveLens;
  lens->set_min_fov((float)ConfigVariableInt("fov", 75) / (4./3.));
  lens->set_aspect_ratio((4./3.));
  PT(Camera) cam = new Camera("cam");
  cam->set_lens(lens);
  cam->set_camera_mask(BitMask32::bit(1));
  camera = scene_root.attach_new_node(cam);
  region->set_camera(camera);

  globals = new Globals;
  globals->camera = camera;
  globals->render = scene_root;
  globals->input = &input;
  globals->win = window;

  PhysSystem::ptr()->initialize();
  physics_world = new PhysScene;
  physics_world->set_gravity(LVector3(0, 0, -800));
  physics_world->set_fixed_timestep(0.15);
  globals->physics_world = physics_world;

  engine->open_windows();

  input.initialize(window);

  load_level("levels/test_foundry");

  world = new World;
  world->spawn();

  player = new Player;

  ClockObject *clock = ClockObject::get_global_clock();

  toon = NodePath(loader->load_sync("models/toon/dogm"));
  toon.reparent_to(scene_root);
  Character *tchar = DCAST(CharacterNode, toon.find("**/+CharacterNode").node())->get_character();
  tchar->loop(0, true);
  toon.set_effect(MapLightingEffect::make(BitMask32::bit(1), false));
  toon.set_scale(16);
  toon.set_h(180);

  scene_root.ls();

  //start_mouse_movement();

  bool pause_was_down = input.get_button_value(IC_pause);

  while (!window->is_closed()) {
    bool pause_down = input.get_button_value(IC_pause);
    if (pause_down) {
      if (!pause_was_down) {
        toggle_mouse();
        pause_was_down = true;
      }
    } else {
      pause_was_down = false;
    }
    physics_world->simulate(clock->get_frame_time());
    input.update();
    EventHandler::get_global_event_handler()->process_events();
    player->move_player();
    calc_view();
    engine->render_frame();
  }

  return 0;
}

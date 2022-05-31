/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfClientBase.cxx
 * @author brian
 * @date 2022-05-03
 */

#include "tfClientBase.h"
#include "graphicsEngine.h"
#include "graphicsPipeSelection.h"
#include "frameBufferProperties.h"
#include "windowProperties.h"
#include "displayRegion.h"
#include "config_tfclient.h"
#include "perspectiveLens.h"
#include "orthographicLens.h"
#include "camera.h"
#include "audioManager.h"
#include "postProcess.h"
#include "asyncTaskManager.h"
#include "eventHandler.h"
#include "event.h"
#include "simulationManager.h"
#include "pStatClient.h"

TFClientBase *cbase = nullptr;

/**
 *
 */
TFClientBase::
TFClientBase() :
  AppBase("tf2-client"),
  _state(S_init),
  _graphics_engine(GraphicsEngine::get_global_ptr()),
  _graphics_output(nullptr),
  _prev_aspect_ratio(0.0f)
{
}

/**
 *
 */
bool TFClientBase::
initialize() {
  if (want_pstats) {
    PStatClient::connect();
  }

  if (!init_display()) {
    return false;
  }

  if (!init_audio()) {
    return false;
  }

  init_physics();

  PT(GenericAsyncTask) eventloop_task = new GenericAsyncTask("eventloop", task_eventloop, this);
  eventloop_task->set_sort(TS_eventloop);
  _task_mgr->add(eventloop_task);

  NetAddress addr;
  addr.set_host("127.0.0.1", 6667);
  _net = new ClientRepository;
  get_cr()->connect(addr);

  return true;
}

/**
 * Initializes all graphics related systems and objects.  Creates a
 * GraphicsPipe, an output window under that pipe, and display regions
 * for 3-D and 2-D scenes.
 */
bool TFClientBase::
init_display() {
  GraphicsPipeSelection *gps = GraphicsPipeSelection::get_global_ptr();
  _graphics_pipe = gps->make_default_pipe();
  if (_graphics_pipe == nullptr) {
    return false;
  }

  // Create the output window that we will display to.
  GraphicsEngine *gengine = GraphicsEngine::get_global_ptr();
  _graphics_output = gengine->make_output(
    _graphics_pipe, "tf-output", 0, FrameBufferProperties::get_default(),
    WindowProperties::get_default(), GraphicsPipe::BF_require_window);
  if (_graphics_output == nullptr) {
    return false;
  }
  _graphics_output->disable_clears();

  // The first display region is the background 3-D skybox.
  // It handles clearing depth for the main 3-D display region.
  _display_region_sky3d = _graphics_output->make_display_region();
  _display_region_sky3d->disable_clears();
  _display_region_sky3d->set_clear_depth_active(true);
  _display_region_sky3d->set_sort(0);

  // Create display region for main 3-D scene.
  _display_region3d = _graphics_output->make_display_region();
  _display_region3d->disable_clears();
  _display_region3d->set_sort(1);

  // View model display region, it renders on top of the main scene
  // with depth cleared, but behind the 2-D scene.
  _display_region_viewmodel = _graphics_output->make_display_region();
  _display_region_viewmodel->disable_clears();
  _display_region_viewmodel->set_clear_depth_active(true);
  _display_region_viewmodel->set_sort(2);

  // Finally, the display region for 2-D scene.
  _display_region2d = _graphics_output->make_display_region();
  _display_region2d->disable_clears();
  _display_region2d->set_clear_depth_active(true);
  _display_region2d->set_sort(3);

  _render = NodePath("render");
  _render_sky3d = NodePath("render_sky3d");
  _render_viewmodel = NodePath("render_viewmodel");

  _lens_3d = new PerspectiveLens;
  _lens_3d->set_min_fov((PN_stdfloat)fov / (4.0f / 3.0f));

  PT(Camera) cam_3d = new Camera("cam");
  cam_3d->set_lens(_lens_3d);
  _camera = _render.attach_new_node("camera");
  _cam = _camera.attach_new_node(cam_3d);

  PT(Camera) cam_sky3d = new Camera("sky3d-camera");
  cam_sky3d->set_lens(_lens_3d);
  _cam_sky3d = _render_sky3d.attach_new_node(cam_sky3d);

  _lens_viewmodel = new PerspectiveLens;
  _lens_viewmodel->set_min_fov((PN_stdfloat)viewmodel_fov / (4.0f / 3.0f));

  PT(Camera) cam_viewmodel = new Camera("viewmodel-camera");
  cam_viewmodel->set_lens(_lens_viewmodel);
  _cam_viewmodel = _render_viewmodel.attach_new_node(cam_viewmodel);

  _display_region_sky3d->set_camera(_cam_sky3d);
  _display_region3d->set_camera(_cam);
  _display_region_viewmodel->set_camera(_cam_viewmodel);

  _hidden = NodePath("hidden");

  // Spawn a task to render at the end of every frame.
  PT(GenericAsyncTask) igloop_task = new GenericAsyncTask("igloop", task_igloop, this);
  igloop_task->set_sort(TS_igloop);
  _task_mgr->add(igloop_task);

  // Intercept the "window-event" event that gets thrown when something on
  // the window changes, such as size or position on screen.  We intercept
  // this to adjust the aspect ratio.
  _event_handler->add_hook("window-event", event_window_event, this);

  gengine->open_windows();

  update_aspect_ratio(get_aspect_ratio());

  return true;
}

/**
 * Initializes the audio system.  Creates AudioManagers for SFX and music.
 */
bool TFClientBase::
init_audio() {
  _sfx_manager = AudioManager::create_AudioManager();
  _sfx_manager->set_volume(sfx_volume);
  _music_manager = AudioManager::create_AudioManager();
  _music_manager->set_volume(music_volume);
  // Spawn a task to pump the audio managers every frame.
  PT(GenericAsyncTask) audioloop_task = new GenericAsyncTask("audioloop", task_audioloop, this);
  audioloop_task->set_sort(TS_audioloop);
  _task_mgr->add(audioloop_task);
  return true;
}

/**
 *
 */
void TFClientBase::
event_window_event(const Event *event, void *data) {
  TFClientBase *base = (TFClientBase *)data;
  if (event->get_num_parameters() == 1) {
    EventParameter param = event->get_parameter(0);
    const GraphicsOutput *win;
    DCAST_INTO_V(win, param.get_ptr());

    if (win == base->_graphics_output) {
      if (!win->is_valid()) {
        // Main window was closed.  Exit the game.
        base->_exit_flag = true;

      } else {
        // Adjust aspect ratio to new window dimensions, if it changed.
        base->update_aspect_ratio(base->get_aspect_ratio());
      }
    }
  }
}

/**
 *
 */
void TFClientBase::
update_aspect_ratio(PN_stdfloat ratio) {
  if (ratio != _prev_aspect_ratio) {
    _prev_aspect_ratio = ratio;
    if (_lens_3d != nullptr) {
      _lens_3d->set_aspect_ratio(ratio);
    }
    if (_lens_viewmodel != nullptr) {
      _lens_viewmodel->set_aspect_ratio(ratio);
    }
  }
}

/**
 * Returns the current aspect ratio of the window.  That is, the width divided
 * by the height.
 */
PN_stdfloat TFClientBase::
get_aspect_ratio() const {
  PN_stdfloat ratio = 1.0f;
  if (_graphics_output != nullptr && _graphics_output->has_size() &&
      _graphics_output->get_sbs_left_y_size() != 0) {
    ratio = (PN_stdfloat)_graphics_output->get_sbs_left_x_size() / (PN_stdfloat)_graphics_output->get_sbs_left_y_size();
  }
  if (ratio == 0.0f) {
    ratio = 1.0f;
  }
  return ratio;
}

/**
 *
 */
void TFClientBase::
do_frame() {
  _sim_mgr->update(_clock);
  _task_mgr->poll();
}

/**
 *
 */
AsyncTask::DoneStatus TFClientBase::
task_eventloop(GenericAsyncTask *task, void *data) {
  TFClientBase *base = (TFClientBase *)data;
  base->_event_handler->process_events();
  return AsyncTask::DS_cont;
}

/**
 *
 */
AsyncTask::DoneStatus TFClientBase::
task_igloop(GenericAsyncTask *task, void *data) {
  TFClientBase *base = (TFClientBase *)data;
  base->_graphics_engine->render_frame();
  return AsyncTask::DS_cont;
}

/**
 *
 */
AsyncTask::DoneStatus TFClientBase::
task_audioloop(GenericAsyncTask *task, void *data) {
  TFClientBase *base = (TFClientBase *)data;
  base->_sfx_manager->update();
  base->_music_manager->update();
  return AsyncTask::DS_cont;
}

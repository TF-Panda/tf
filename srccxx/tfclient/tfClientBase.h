/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfClientBase.h
 * @author brian
 * @date 2022-05-03
 */

#ifndef TFCLIENTBASE_H
#define TFCLIENTBASE_H

#include "pandabase.h"
#include "pointerTo.h"
#include "nodePath.h"
#include "audioManager.h"
#include "postProcess.h"
#include "clientRepository.h"
#include "appBase.h"

class GraphicsPipe;
class GraphicsOutput;
class DisplayRegion;
class Lens;
class AsyncTaskManager;
class EventHandler;

/**
 *
 */
class TFClientBase : public AppBase {
public:
  enum State {
    S_init,
    S_intro,
    S_preload,
    S_menu,
  };

  enum TaskSort {
    TS_eventloop = -2000,
    TS_igloop = 1000,
    TS_audioloop = 2000,
  };

  TFClientBase();

  virtual bool initialize() override;

  virtual void do_frame() override;

  INLINE GraphicsOutput *get_output() const;
  INLINE GraphicsPipe *get_pipe() const;

  void update_aspect_ratio(PN_stdfloat ratio);
  PN_stdfloat get_aspect_ratio() const;

  INLINE ClientRepository *get_cr() const;

private:
  bool init_display();
  bool init_audio();

  static void event_window_event(const Event *event, void *data);
  static AsyncTask::DoneStatus task_eventloop(GenericAsyncTask *task, void *data);
  static AsyncTask::DoneStatus task_igloop(GenericAsyncTask *task, void *data);
  static AsyncTask::DoneStatus task_audioloop(GenericAsyncTask *task, void *data);

public:
  PN_stdfloat _prev_aspect_ratio;

  PT(PostProcess) _post_process;

  GraphicsEngine *_graphics_engine;
  PT(GraphicsPipe) _graphics_pipe;
  GraphicsOutput *_graphics_output;

  PT(DisplayRegion) _display_region_sky3d;
  PT(DisplayRegion) _display_region3d;
  PT(DisplayRegion) _display_region_viewmodel;
  PT(DisplayRegion) _display_region2d;

  // Shared between 3-D skybox and 3-D world.
  PT(Lens) _lens_3d;
  PT(Lens) _lens_viewmodel;

  NodePath _cam;
  NodePath _camera;
  NodePath _cam_sky3d;
  NodePath _cam_viewmodel;
  NodePath _cam_2d;
  NodePath _render_sky3d;
  NodePath _render_viewmodel;
  NodePath _render2d;
  NodePath _aspect2d;

  PT(AudioManager) _sfx_manager;
  PT(AudioManager) _music_manager;

  State _state;
};

extern TFClientBase *cbase;

#include "tfClientBase.I"

#endif // TFCLIENTBASE_H

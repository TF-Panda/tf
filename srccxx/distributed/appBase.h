/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file appBase.h
 * @author brian
 * @date 2022-05-19
 */

#ifndef APPBASE_H
#define APPBASE_H

#include "tfbase.h"
#include "pointerTo.h"
#include "physScene.h"
#include "asyncTaskManager.h"
#include "clockObject.h"
#include "simulationManager.h"
#include "networkRepository.h"
#include "nodePath.h"
#include "eventHandler.h"
#include "genericAsyncTask.h"

/**
 *
 */
class EXPCL_TF_DISTRIBUTED AppBase {
public:
  AppBase(const std::string &name);

  INLINE ClockObject *get_clock() const;
  INLINE SimulationManager *get_sim_mgr() const;
  INLINE AsyncTaskManager *get_sim_task_mgr() const;
  INLINE AsyncTaskManager *get_task_mgr() const;
  INLINE PhysScene *get_phys_scene() const;
  INLINE const NodePath &get_render() const;
  INLINE const NodePath &get_hidden() const;
  INLINE EventHandler *get_event_handler() const;

  INLINE void set_exit_flag(bool flag);
  INLINE bool get_exit_flag() const;

  INLINE const std::string &get_app_name() const;

  virtual bool initialize();

  void run();
  virtual void do_frame();

  virtual void init_physics();

protected:
  static AsyncTask::DoneStatus phys_update_task(GenericAsyncTask *task, void *data);

public:
  PT(ClockObject) _clock;
  PT(SimulationManager) _sim_mgr;
  PT(PhysScene) _phys_scene;
  PT(AsyncTaskManager) _task_mgr;
  PT(NetworkRepository) _net;
  EventHandler *_event_handler;
  NodePath _render;
  NodePath _hidden;

  bool _exit_flag;

  bool _initialized;

  std::string _app_name;

  PT(GenericAsyncTask) _phys_update_task;
};

extern EXPCL_TF_DISTRIBUTED AppBase *base;

#include "appBase.I"

#endif // APPBASE_H

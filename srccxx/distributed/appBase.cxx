/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file appBase.cxx
 * @author brian
 * @date 2022-05-19
 */

#include "appBase.h"
#include "physSystem.h"

AppBase *base = nullptr;

/**
 *
 */
AppBase::
AppBase(const std::string &name) :
  _clock(ClockObject::get_global_clock()),
  _sim_mgr(new SimulationManager),
  _phys_scene(nullptr),
  _task_mgr(AsyncTaskManager::get_global_ptr()),
  _net(nullptr),
  _event_handler(EventHandler::get_global_event_handler()),
  _render("render"),
  _hidden("hidden"),
  _exit_flag(false),
  _initialized(false),
  _app_name(name),
  _phys_update_task(nullptr)
{
}

/**
 *
 */
bool AppBase::
initialize() {
  init_physics();
  return true;
}

/**
 *
 */
void AppBase::
init_physics() {
  PhysSystem::ptr()->initialize();
  _phys_scene = new PhysScene;
  _phys_scene->set_gravity(LVector3(0.0f, 0.0f, -800.0f));
  _phys_scene->set_fixed_timestep(0.015);
  _phys_update_task = new GenericAsyncTask("physUpdate", phys_update_task, this);
  _phys_update_task->set_sort(30);
  _task_mgr->add(_phys_update_task);
}

/**
 *
 */
AsyncTask::DoneStatus AppBase::
phys_update_task(GenericAsyncTask *task, void *data) {
  AppBase *self = (AppBase *)data;
  self->_phys_scene->simulate(self->_clock->get_frame_time());
  return AsyncTask::DS_cont;
}

/**
 *
 */
void AppBase::
run() {
  while (!_exit_flag) {
    do_frame();
  }
}

/**
 *
 */
void AppBase::
do_frame() {
  _task_mgr->poll();
}

/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file appBase.I
 * @author brian
 * @date 2022-05-19
 */

/**
 * Returns the app's clock.
 */
INLINE ClockObject *AppBase::
get_clock() const {
  return _clock;
}

/**
 *
 */
INLINE SimulationManager *AppBase::
get_sim_mgr() const {
  return _sim_mgr;
}

/**
 *
 */
INLINE AsyncTaskManager *AppBase::
get_sim_task_mgr() const {
  return _sim_mgr->get_task_mgr();
}

/**
 *
 */
INLINE AsyncTaskManager *AppBase::
get_task_mgr() const {
  return _task_mgr;
}

/**
 *
 */
INLINE PhysScene *AppBase::
get_phys_scene() const {
  return _phys_scene;
}

/**
 *
 */
INLINE const NodePath &AppBase::
get_render() const {
  return _render;
}

/**
 *
 */
INLINE const NodePath &AppBase::
get_hidden() const {
  return _hidden;
}

/**
 *
 */
INLINE EventHandler *AppBase::
get_event_handler() const {
  return _event_handler;
}

/**
 *
 */
INLINE void AppBase::
set_exit_flag(bool flag) {
  _exit_flag = flag;
}

/**
 *
 */
INLINE bool AppBase::
get_exit_flag() const {
  return _exit_flag;
}

/**
 *
 */
INLINE const std::string &AppBase::
get_app_name() const {
  return _app_name;
}

/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file simulationManager.I
 * @author brian
 * @date 2022-05-08
 */

/**
 *
 */
INLINE void SimulationManager::
set_tick_rate(PN_stdfloat ticks_per_sec) {
  nassertv(ticks_per_sec > 0.0f);
  _ticks_per_sec = ticks_per_sec;
  _interval_per_tick = 1.0f / ticks_per_sec;
}

/**
 *
 */
INLINE PN_stdfloat SimulationManager::
get_tick_rate() const {
  return _ticks_per_sec;
}

/**
 *
 */
INLINE PN_stdfloat SimulationManager::
get_interval_per_tick() const {
  return _interval_per_tick;
}

/**
 *
 */
INLINE uint32_t SimulationManager::
get_tick_count() const {
  return _tick_count;
}

/**
 *
 */
INLINE PN_stdfloat SimulationManager::
ticks_to_time(uint32_t tick) const {
  return tick * _interval_per_tick;
}

/**
 *
 */
INLINE uint32_t SimulationManager::
time_to_ticks(PN_stdfloat time) const {
  return (uint32_t)(0.5f + time / _interval_per_tick);
}

/**
 *
 */
INLINE bool SimulationManager::
is_final_tick() const {
  return is_in_simulation() && _current_ticks_this_frame == _total_ticks_this_frame;
}

/**
 *
 */
INLINE bool SimulationManager::
is_in_simulation() const {
  return _in_simulation;
}

/**
 *
 */
INLINE AsyncTaskManager *SimulationManager::
get_task_mgr() const {
  return _task_mgr;
}

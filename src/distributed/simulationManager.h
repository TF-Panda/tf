/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file simulationManager.h
 * @author brian
 * @date 2022-05-08
 */

#ifndef SIMULATIONMANAGER_H
#define SIMULATIONMANAGER_H

#include "tfbase.h"
#include "numeric_types.h"
#include "asyncTaskManager.h"
#include "referenceCount.h"

class ClockObject;

/**
 * Manages a fixed-timestep simulation.
 */
class EXPCL_TF_DISTRIBUTED SimulationManager : public ReferenceCount {
PUBLISHED:
  SimulationManager();

  INLINE void set_tick_rate(PN_stdfloat ticks_per_sec);
  INLINE PN_stdfloat get_tick_rate() const;
  INLINE PN_stdfloat get_interval_per_tick() const;

  INLINE uint32_t get_tick_count() const;

  INLINE PN_stdfloat ticks_to_time(uint32_t tick) const;
  INLINE uint32_t time_to_ticks(PN_stdfloat time) const;

  INLINE bool is_final_tick() const;
  INLINE bool is_in_simulation() const;

  INLINE AsyncTaskManager *get_task_mgr() const;

  void update(ClockObject *clock);

  void set_temp_clock(int frame, double frame_time, double dt);
  void restore_clock();

private:
  PN_stdfloat _ticks_per_sec;
  PN_stdfloat _interval_per_tick;
  PN_stdfloat _remainder;
  PN_stdfloat _frame_time;
  uint32_t _tick_count;
  int _current_frame_tick;
  int _current_ticks_this_frame;
  int _total_ticks_this_frame;
  bool _in_simulation;
  // For tasks that should run during simulation steps.
  PT(AsyncTaskManager) _task_mgr;

  unsigned int _save_tick_count;
  double _save_frame_time;
  double _save_dt;
  ClockObject::Mode _save_mode;
};

#include "simulationManager.I"

#endif // SIMULATIONMANAGER_H

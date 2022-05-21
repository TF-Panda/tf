/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file simulationManager.cxx
 * @author brian
 * @date 2022-05-08
 */

#include "simulationManager.h"
#include "clockObject.h"
#include "cmath.h"

/**
 *
 */
SimulationManager::
SimulationManager() :
  _ticks_per_sec(60.0f),
  _interval_per_tick(1.0f / 60.0f),
  _remainder(0.0f),
  _frame_time(0.0f),
  _tick_count(0),
  _current_frame_tick(0),
  _current_ticks_this_frame(0),
  _in_simulation(false),
  _task_mgr(new AsyncTaskManager("sim"))
{
}

/**
 *
 */
void SimulationManager::
update(ClockObject *clock) {
  PN_stdfloat dt = clock->get_dt();
  int frame_count = clock->get_frame_count();

  _in_simulation = true;

  _remainder += dt;

  int num_ticks = 0;
  if (_remainder >= _interval_per_tick) {
    num_ticks = (int)cfloor(_remainder / _interval_per_tick);
    _remainder -= num_ticks * _interval_per_tick;
  }

  _total_ticks_this_frame = num_ticks;
  _current_ticks_this_frame = 0;
  _current_frame_tick = 0;

  ClockObject::Mode orig_mode = clock->get_mode();
  clock->set_mode(ClockObject::M_slave);

  for (int i = 0; i < num_ticks; ++i) {
    ++_current_ticks_this_frame;

    _frame_time = _interval_per_tick * _tick_count;
    clock->set_frame_time(_frame_time);
    clock->set_dt(_interval_per_tick);
    clock->set_frame_count(_tick_count);

    _task_mgr->poll();

    ++_tick_count;
    ++_current_frame_tick;
  }

  clock->set_frame_time(_tick_count * _interval_per_tick + _remainder);
  clock->set_dt(dt);
  clock->set_frame_count(frame_count);
  clock->set_mode(orig_mode);

  _in_simulation = false;
}

/**
 *
 */
void SimulationManager::
set_temp_clock(int frame, double frame_time, double dt) {
  nassertv(_in_simulation);

  ClockObject *clock = ClockObject::get_global_clock();
  _save_mode = clock->get_mode();
  _save_tick_count = clock->get_frame_count();
  _save_frame_time = clock->get_frame_time();
  _save_dt = clock->get_dt();

  clock->set_mode(ClockObject::M_slave);
  clock->set_frame_count(frame);
  clock->set_frame_time(frame_time);
  clock->set_dt(dt);

  _tick_count = frame;
  _frame_time = frame_time;
}

/**
 *
 */
void SimulationManager::
restore_clock() {
  nassertv(_in_simulation);

  ClockObject *clock = ClockObject::get_global_clock();
  clock->set_frame_count(_save_tick_count);
  clock->set_frame_time(_save_frame_time);
  clock->set_dt(_save_dt);
  clock->set_mode(_save_mode);

  _tick_count = _save_tick_count;
  _frame_time = _save_frame_time;
}

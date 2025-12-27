#include "simulationManager.h"
#include "clockObject.h"
#include "cmath.h"

/**
 *
 */
void
SimulationManager::run_frame() {
  ClockObject *clock = ClockObject::get_global_clock();

  float dt = clock->get_dt();

  _prev_accum_time = _accum_time;
  if (_prev_accum_time < 0.0f) {
    _prev_accum_time = 0.0f;
  }

  _accum_time += dt;

  float tick_interval = get_tick_interval();

  int num_ticks_to_run = cfloor(_accum_time / tick_interval);

  _accum_time -= num_ticks_to_run * tick_interval;

  for (int i = 0; i < num_ticks_to_run; ++i) {
    run_simulation();
  }
}

/**
 *
 */
void
SimulationManager::run_simulation() {
}

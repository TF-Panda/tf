#include "simulationManager.h"
#include "clockObject.h"
#include "cmath.h"

/**
 * Runs any simulation ticks for this rendering frame/epoch.
 */
void
SimulationManager::run_frame() {
  ClockObject *clock = ClockObject::get_global_clock();

  // We shouldn't be in a simulation clock outside of the main simulation update.
  nassertv(!is_in_simulation_clock());

  float frame_dt = clock->get_dt();

  // TODO: Clock drift manager.
  bool has_clock_drift_mgr = false;

  _prev_accum_time = _accum_time;
  if (_prev_accum_time < 0.0f) {
    _prev_accum_time = 0.0f;
  }

  _accum_time += frame_dt;

  float tick_interval = get_tick_interval();

  int num_ticks_to_run = cfloor(_accum_time / tick_interval);

  _accum_time -= num_ticks_to_run * tick_interval;

  if (num_ticks_to_run > 0) {
    calc_simulation_delta(num_ticks_to_run + _tick_count);
  }

  _total_ticks_this_frame = num_ticks_to_run;
  _current_frame_tick = 0;
  _current_ticks_this_frame = 1;

  for (int i = 0; i < num_ticks_to_run; ++i) {
    float tick_dt;
    if (has_clock_drift_mgr) {
      tick_dt = frame_dt;
    } else {
      tick_dt = (_tick_count - _prev_tick_count) * get_tick_interval();
    }

    enter_simulation_time(_tick_count, -1, tick_dt);
    set_restore_tick_count(false);

    _sim_interrupted = false;

    // Actually run simulation.
    run_simulation();

    if (_sim_interrupted) {
      exit_simulation_time();
      break;
    }

    _prev_tick_count = _tick_count;

    exit_simulation_time();

    ++_tick_count;
    ++_current_frame_tick;
    ++_current_ticks_this_frame;
  }

  nassertv(!is_in_simulation_clock());
}

/**
 *
 */
void SimulationManager::
run_simulation() {
}

/**
 *
 */
void SimulationManager::
calc_simulation_delta(int tick) {
  _simulation_delta = get_client_frame_time() - ((tick * get_tick_interval()) + _accum_time);
  _simulation_delta_no_remainder = get_client_frame_time() - (tick * get_tick_interval());
}

/**
 *
 */
float SimulationManager::
get_network_time() const {
  if (is_in_simulation_clock()) {
    // If we're in simulation, the clock contains the client-space simulation time,
    // so subtract the delta to get the network space time.
    return _clock->get_frame_time() - _simulation_delta;
  } else {
    // Return current ticks to time.
    return _tick_count * get_tick_interval();
  }
}

/**
 * Returns the current client simulation time.  This is the simulation time adjusted
 * for the client's frame clock.
 */
float SimulationManager::
get_client_simulation_time() const {
  if (is_in_simulation_clock()) {
    // If we're in simulation, return the frame time on the clock directly, as it
    // contains our client-space simulation time directly.
    return _clock->get_frame_time();
  } else {
    // Not in simulation, so convert current network time to client simulation time.
    return get_network_time() + _simulation_delta;
  }
}

/**
 *
 */
float SimulationManager::
get_client_frame_time() const {
  if (is_in_simulation_clock()) {
    return _saved_stack.front().frame_time;
  } else {
    return _clock->get_frame_time();
  }
}

/**
 *
 */
float SimulationManager::
network_to_client_time(float network_time) const {
  return network_time + _simulation_delta;
}

/**
 *
 */
float SimulationManager::
client_to_network_time(float client_time) const {
  return client_time - _simulation_delta;
}

/**
 *
 */
float SimulationManager::
get_time() const {
#ifdef CLIENT
  if (is_in_simulation_clock() /*&& is_in_prediction())*/) {
    return _clock->get_frame_time() - _simulation_delta;
  } else {
    return _clock->get_frame_time();
  }
#else
  return _clock->get_frame_time();
#endif
}

/**
 *
 */
float SimulationManager::
get_client_time() const {
  return _clock->get_frame_time();
}

/**
 *
 */
float SimulationManager::
get_delta_time() const {
  return _clock->get_dt();
}

/**
 *
 */
void SimulationManager::
set_restore_tick_count(bool flag) {
  if (!_saved_stack.empty()) {
    _saved_stack.back().restore_tick_count = flag;
  }
}

/**
 *
 */
void SimulationManager::
enter_simulation_time(int tick_number, int time_tick, float dt) {
  if (time_tick < 0) {
    time_tick = tick_number;
  }
  if (dt < 0.0f) {
    dt = get_tick_interval();
  }
  ClockState state;
  state.tick_count = _tick_count;
  state.frame_time = _clock->get_frame_time();
  state.dt = _clock->get_dt();
  state.frame_count = _clock->get_frame_count();
  state.mode = _clock->get_mode();
  state.restore_tick_count = true;
  _saved_stack.push_back(std::move(state));
  _tick_count = tick_number;
  _clock->set_mode(ClockObject::M_slave);
  _clock->set_frame_time((time_tick * get_tick_interval()) + _simulation_delta);
  _clock->set_dt(dt);
  _clock->set_frame_count(_tick_count);
  ++_simulation_depth;
}

/**
 *
 */
void SimulationManager::
exit_simulation_time() {
  nassertv(_simulation_depth > 0);

  ClockState state = _saved_stack.back();
  _saved_stack.pop_back();

  if (state.restore_tick_count) {
    _tick_count = state.tick_count;
  }
  _clock->set_mode(ClockObject::M_slave);
  _clock->set_frame_time(state.frame_time);
  _clock->set_dt(state.dt);
  _clock->set_frame_count(state.frame_count);
  _clock->set_mode(state.mode);
  --_simulation_depth;
}

/**
 *
 */
void SimulationManager::
reset_simulation(int tick) {
  _prev_tick_count = tick;
  _tick_count = tick;
  _sim_interrupted = true;
  _accum_time = 0.0f;
  _prev_accum_time = 0.0f;
  set_restore_tick_count(false);
  calc_simulation_delta(tick);
}

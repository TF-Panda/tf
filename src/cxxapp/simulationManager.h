#ifndef SIMULATIONMANAGER_H
#define SIMULATIONMANAGER_H

#include "pandabase.h"
#include "clockObject.h"
#include "pvector.h"

/**
 *
 */
class SimulationManager {
public:
  /**
   * Saved clock state when we switch contexts.
   */
  struct ClockState {
    int tick_count;
    float frame_time;
    float dt;
    int frame_count;
    ClockObject::Mode mode;
    bool restore_tick_count;
  };

  inline SimulationManager();

  void run_frame();
  virtual void run_simulation();

  inline void set_tick_rate(int rate);

  inline size_t get_tick_count() const;
  inline int get_tick_rate() const;
  inline float get_tick_interval() const;

  inline void set_simulation_delta(float delta);
  void calc_simulation_delta(int tick);
  inline bool is_in_simulation_clock() const;
  float get_network_time() const;
  float get_client_simulation_time() const;
  float get_client_frame_time() const;
  float network_to_client_time(float network_time) const;
  float client_to_network_time(float client_time) const;
  float get_time() const;
  float get_client_time() const;
  float get_delta_time() const;
  void set_restore_tick_count(bool flag);
  void enter_simulation_time(int tick_number, int time_tick = -1, float dt = -1.0f);
  void exit_simulation_time();

protected:
  size_t _tick_count;
  int _tick_rate;
  float _accum_time;
  float _prev_accum_time;

  ClockObject *_clock;
  float _simulation_delta;
  float _simulation_delta_no_remainder;
  int _simulation_depth;

  int _prev_tick_count;
  int _total_ticks_this_frame;
  int _current_frame_tick;
  int _current_ticks_this_frame;

  pvector<ClockState> _saved_stack;
};

/**
 *
 */
inline SimulationManager::
SimulationManager() :
  _tick_count(0u), _tick_rate(30), _accum_time(0.0f), _prev_accum_time(0.0f),
  _simulation_delta(0.0f),
  _simulation_delta_no_remainder(0.0f),
  _simulation_depth(0),
  _prev_tick_count(0),
  _total_ticks_this_frame(0),
  _current_frame_tick(0),
  _current_ticks_this_frame(0),
  _clock(ClockObject::get_global_clock())
{
}

/**
 *
 */
inline void
SimulationManager::set_tick_rate(int rate) {
  _tick_rate = rate;
}

/**
 *
 */
inline size_t
SimulationManager::get_tick_count() const {
  return _tick_count;
}

/**
 *
 */
inline int
SimulationManager::get_tick_rate() const {
  return _tick_rate;
}

/**
 *
 */
inline float
SimulationManager::get_tick_interval() const {
  return 1.0f / (float)_tick_rate;
}

/**
 *
 */
inline void SimulationManager::
set_simulation_delta(float delta) {
  _simulation_delta = delta;
}

/**
 *
 */
inline bool SimulationManager::
is_in_simulation_clock() const {
  return _simulation_depth > 0;
}


#endif // SIMULATIONMANAGER_H

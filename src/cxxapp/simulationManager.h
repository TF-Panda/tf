#ifndef SIMULATIONMANAGER_H
#define SIMULATIONMANAGER_H

#include "pandabase.h"

/**
 *
 */
class SimulationManager {
public:
  inline SimulationManager();

  void run_frame(); 
  virtual void run_simulation();

  inline void set_tick_rate(int rate);
  
  inline size_t get_tick_count() const;
  inline int get_tick_rate() const;
  inline float get_tick_interval() const;

protected:
  size_t _tick_count;
  int _tick_rate;
  float _accum_time;
  float _prev_accum_time;
  
};

/**
 *
 */
inline SimulationManager::SimulationManager() :
  _tick_count(0u), _tick_rate(30), _accum_time(0.0f), _prev_accum_time(0.0f) {
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

#endif // SIMULATIONMANAGER_H

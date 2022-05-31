/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfAIBase.cxx
 * @author brian
 * @date 2022-05-09
 */

#include "tfAIBase.h"
#include "configVariableInt.h"
#include "pStatClient.h"
#include "clockObject.h"
#include "asyncTaskManager.h"
#include "config_tfai.h"
#include "tfGlobals.h"
#include "simulationManager.h"

TFAIBase *simbase = nullptr;

ConfigVariableInt server_port("server-port", 6667);
ConfigVariableDouble server_tick_rate("server-tick-rate", 66);
ConfigVariableBool server_want_pstats("server-want-pstats", false);

TFAIBase::
TFAIBase() :
  AppBase("tf2-server")
{
}

/**
 *
 */
bool TFAIBase::
initialize() {
  if (server_want_pstats) {
    PStatClient::connect();
  }

  AppBase::initialize();

  tfai_cat.info()
    << "Simulation rate: " << server_tick_rate << " ticks/sec\n";
  _sim_mgr->set_tick_rate(server_tick_rate);

  //PT(ServerRepository) air = new ServerRepository;
  //air->open_server(server_port);
  _net = new ServerRepository;
  //((ServerRepository *)_net.p())->open_server(server_port);
  get_air()->open_server(server_port.get_value());

  return true;
}

/**
 *
 */
void TFAIBase::
do_frame() {
  // First tick the clock.  Note on the client this happens in igLoop *after*
  // simulation for the frame.
  _clock->tick();

  // Tick the PStat profiler if it's running.
  PStatClient::main_tick();

  // Run any simulation ticks.  This steps the simulation task manager each
  // tick.
  _sim_mgr->update(_clock);

  // Now step per-frame tasks.  This task list is most likely completely
  // empty on the server.
  _task_mgr->poll();

  // Sleep for a fraction of the tick remainder to lessen CPU load.
  double elapsed = _clock->get_real_time() - _clock->get_frame_time();
  double remainder = (_sim_mgr->get_interval_per_tick() - elapsed) * 0.5;
  if (remainder > 0.0) {
    Thread::sleep(remainder);
  }
}

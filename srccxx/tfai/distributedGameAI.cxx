/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedGameAI.cxx
 * @author brian
 * @date 2022-05-09
 */

#include "distributedGameAI.h"
#include "networkClass.h"
#include "networkedObjectRegistry.h"
#include "clockObject.h"

IMPLEMENT_CLASS(DistributedGameAI);

NET_CLASS_DEF_BEGIN_NOBASE(DistributedGameAI)
  _network_class->add_field(
    new NetworkField("round", NET_OFFSET(DistributedGameAI, _round),
                     NetworkField::NDT_int, NetworkField::DT_uint8));
  _network_class->add_field(
    new NetworkField("num_rounds", NET_OFFSET(DistributedGameAI, _num_rounds),
                     NetworkField::NDT_int, NetworkField::DT_uint8));
  _network_class->add_field(
    new NetworkField("round_time_remaining", NET_OFFSET(DistributedGameAI, _round_time_remaining),
                     NetworkField::NDT_float, NetworkField::DT_float32));
  _network_class->add_field(
    new NetworkField("team_scores", NET_OFFSET(DistributedGameAI, _team_scores),
                     NetworkField::NDT_int, NetworkField::DT_uint8, (int)TFTeam::COUNT));
NET_CLASS_DEF_END()


/**
 *
 */
void DistributedGameAI::
generate() {
  DistributedObjectAI::generate();
  _round = 0;
  _num_rounds = 3;
  _team_scores[0] = 0;
  _team_scores[1] = 5;
  _round_time_remaining = 5 * 60.0f;
}
/**
 *
 */
void DistributedGameAI::
announce_generate() {
  DistributedObjectAI::announce_generate();
  add_sim_task("decRoundTime", dec_time_task);
}

/**
 *
 */
AsyncTask::DoneStatus DistributedGameAI::
dec_time_task(GenericAsyncTask *task, void *data) {
  DistributedGameAI *self = (DistributedGameAI *)data;
  ClockObject *clock = ClockObject::get_global_clock();
  self->_round_time_remaining -= clock->get_dt();
  //std::cout << self->_round_time_remaining << "\n";
  return AsyncTask::DS_cont;
}

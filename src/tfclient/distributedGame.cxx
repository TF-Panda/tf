/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedGame.cxx
 * @author brian
 * @date 2022-05-19
 */

#include "distributedGame.h"
#include "tfGlobals.h"
#include "networkedObjectRegistry.h"
#include "networkClass.h"

IMPLEMENT_CLASS(DistributedGame);

NET_CLASS_DEF_BEGIN_NOBASE(DistributedGame)
  _network_class->add_field(
    new NetworkField("round", NET_OFFSET(DistributedGame, _round),
                     NetworkField::NDT_int, NetworkField::DT_uint8));
  _network_class->add_field(
    new NetworkField("num_rounds", NET_OFFSET(DistributedGame, _num_rounds),
                     NetworkField::NDT_int, NetworkField::DT_uint8));
  _network_class->add_field(
    new NetworkField("round_time_remaining", NET_OFFSET(DistributedGame, _round_time_remaining),
                     NetworkField::NDT_float, NetworkField::DT_float32));
  _network_class->add_field(
    new NetworkField("team_scores", NET_OFFSET(DistributedGame, _team_scores),
                     NetworkField::NDT_int, NetworkField::DT_uint8, (int)TFTeam::COUNT));
NET_CLASS_DEF_END()

/**
 *
 */
void DistributedGame::
pre_data_update(bool generate) {
  DistributedObject::pre_data_update(generate);
  std::cout << "Pre data update on DGame, " << generate << "\n";
}

/**
 *
 */
void DistributedGame::
post_data_update(bool generate) {
  DistributedObject::post_data_update(generate);
  std::cout << "Post data update on DGame, " << generate << "\n";
}

/**
 *
 */
void DistributedGame::
generate() {
  DistributedObject::generate();
  std::cout << "Generate() on dGame\n";
  std::cout << "round " << _round << "\n";
  std::cout << "num rounds " << _num_rounds << "\n";
  std::cout << "time " << _round_time_remaining << "\n";
}

/**
 *
 */
void DistributedGame::
announce_generate() {
  DistributedObject::announce_generate();
  std::cout << "announce_generate() on DGame\n";
  std::cout << "round " << _round << "\n";
  std::cout << "num rounds " << _num_rounds << "\n";
  std::cout << "time " << _round_time_remaining << "\n";
}

/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedGameAI.h
 * @author brian
 * @date 2022-05-09
 */

#ifndef DISTRIBUTEDGAMEAI_H
#define DISTRIBUTEDGAMEAI_H

#include "pandabase.h"
#include "distributedObjectAI.h"
#include "tfGlobals.h"
#include "pointerTo.h"
#include "pmap.h"
#include "genericAsyncTask.h"

class DistributedTFPlayerAI;

/**
 * TF2 game manager.
 */
class DistributedGameAI : public DistributedObjectAI {
  DECLARE_CLASS(DistributedGameAI, DistributedObjectAI);
  NET_CLASS_DECL(DistributedGameAI);

public:
  //PT(DistributedTFPlayerAI) create_player();

  virtual void generate() override;
  virtual void announce_generate() override;

  INLINE const std::string &get_level_name() const;

  static AsyncTask::DoneStatus dec_time_task(GenericAsyncTask *task, void *data);

private:
  int _round;
  int _num_rounds;
  float _round_time_remaining;
  // Counts # of rounds won by each team.
  int _team_scores[(int)TFTeam::COUNT];

  std::string _level_name;
};

#include "distributedGameAI.I"

#endif // DISTRIBUTEDGAMEAI_H

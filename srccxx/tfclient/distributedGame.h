/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedGame.h
 * @author brian
 * @date 2022-05-19
 */

#ifndef DISTRIBUTEDGAME_H
#define DISTRIBUTEDGAME_H

#include "tfbase.h"
#include "distributedObject.h"
#include "tfGlobals.h"

/**
 *
 */
class DistributedGame : public DistributedObject {
  DECLARE_CLASS(DistributedGame, DistributedObject);
  NET_CLASS_DECL(DistributedGame);

public:
  DistributedGame() = default;

  virtual void pre_data_update(bool generate) override;
  virtual void post_data_update(bool generate) override;
  virtual void generate() override;
  virtual void announce_generate() override;

private:
  int _round;
  int _num_rounds;
  float _round_time_remaining;
  // Counts # of rounds won by each team.
  int _team_scores[(int)TFTeam::COUNT];
};

#include "distributedGame.I"

#endif // DISTRIBUTEDGAME_H

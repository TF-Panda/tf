/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfai_main.cxx
 * @author brian
 * @date 2022-05-09
 */

#include "tfAIBase.h"

#include "tfai_types.h"
#include "tfai_netclasses.h"

#include "distributedGameAI.h"
#include "distributedEntityAI.h"

/**
 *
 */
int
main(int argc, char *argv[]) {
  init_ai_types();
  init_ai_net_classes();

  TFAIBase tbase;
  base = &tbase;
  simbase = &tbase;
  tbase.initialize();

  DistributedGameAI *game = new DistributedGameAI;
  tbase.get_air()->generate_object(game, 0);

  PT(DistributedEntityAI) ent = new DistributedEntityAI;
  ent->set_pos(LPoint3(0, -950, 64));
  tbase.get_air()->generate_object(ent, 0);

  tbase.run();

  return 0;
}

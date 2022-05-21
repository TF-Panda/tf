/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfai_netclasses.cxx
 * @author brian
 * @date 2022-05-12
 */

#include "tfai_netclasses.h"
#include "networkedObjectRegistry.h"

#include "distributedGameAI.h"

/**
 *
 */
void
init_ai_net_classes() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  DistributedGameAI::init_network_class();

  NetworkedObjectRegistry::get_global_ptr()->output(std::cout);
}

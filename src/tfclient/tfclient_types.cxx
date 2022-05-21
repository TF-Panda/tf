/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfclient_types.cxx
 * @author brian
 * @date 2022-05-18
 */

#include "tfclient_types.h"
#include "clientRepository.h"
#include "distributedObject.h"
#include "distributedGame.h"

/**
 *
 */
void
init_tfclient_types() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  ClientRepository::init_type();
  DistributedObject::init_type();
  DistributedGame::init_type();

  DistributedGame::init_network_class();
}

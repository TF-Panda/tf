/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_tfdistributed.cxx
 * @author brian
 * @date 2022-05-10
 */

#include "config_tfdistributed.h"
#include "networkedObjectBase.h"
#include "networkRepository.h"

ConfigureDef(config_tfdistributed);
ConfigureFn(config_tfdistributed) {
  init_libtfdistributed();
}

NotifyCategoryDef(tfdistributed, "");

/**
 *
 */
void
init_libtfdistributed() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  NetworkedObjectBase::init_type();
  NetworkRepository::init_type();
}

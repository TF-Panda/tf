/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_player.cxx
 * @author brian
 * @date 2022-05-23
 */

#include "config_player.h"

ConfigureDef(config_player);
ConfigureFn(config_player) {
  init_libplayer();
}

/**
 *
 */
void
init_libplayer() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;
}

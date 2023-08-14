/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_tf.cxx
 * @author brian
 * @date 2022-05-23
 */

#include "config_tf.h"

ConfigureDef(config_tf);
ConfigureFn(config_tf) {
  init_libtf();
}

/**
 *
 */
void
init_libtf() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;
}

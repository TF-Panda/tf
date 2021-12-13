/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_tfbase.cxx
 * @author brian
 * @date 2021-11-11
 */

#include "config_tfbase.h"

#if !defined(CPPPARSER) && !defined(LINK_ALL_STATIC) && !defined(BUILDING_TF_TFBASE)
  #error Buildsystem error: BUILDING_TF_TFBASE not defined
#endif

ConfigureDef(config_tfbase);
NotifyCategoryDef(tfbase, "");

ConfigureFn(config_tfbase) {
  init_libtfbase();
}

/**
 * Initializes the library.  This must be called at least once before any of
 * the functions or classes in this library can be used.  Normally it will be
 * called by the static initializers and need not be called explicitly, but
 * special cases exist.
 */
void
init_libtfbase() {
  static bool initialized = false;
  if (initialized) {
    return;
  }

  initialized = true;
}

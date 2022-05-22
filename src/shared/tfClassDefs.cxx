/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfClassDefs.cxx
 * @author brian
 * @date 2022-05-21
 */

#include "tfClassDefs.h"

TFClassDef tf_class_defs[(int)TFClass::COUNT] = {
  // scout
  {
    "models/char/scout",
    "models/weapons/v_scattergun_scout",
    1.33f,
    1.2f,
    0.44f,
    1.07f,
    65,
    125,
    "scout"
  },
  // soldier
  {
    "models/char/soldier",
    "models/weapons/c_soldier_arms",
    0.8f, 0.72f, 0.27f, 0.64f,
    68,
    200,
    "soldier"
  },
};

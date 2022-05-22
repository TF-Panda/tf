/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfClassDefs.h
 * @author brian
 * @date 2022-05-21
 */

#ifndef TFCLASSDEFS_H
#define TFCLASSDEFS_H

#include "tfbase.h"
#include "tfGlobals.h"
#include "filename.h"

struct TFClassDef {
  Filename player_model;
  Filename view_model;
  float fwd;
  float back;
  float crouch;
  float swim;
  float view_height;
  int max_hp;
  std::string phonemes;
};

extern TFClassDef tf_class_defs[(int)TFClass::COUNT];

#endif // TFCLASSDEFS_H

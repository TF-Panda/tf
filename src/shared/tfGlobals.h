/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfGlobals.h
 * @author brian
 * @date 2022-05-09
 */

#ifndef TFGLOBALS_H
#define TFGLOBALS_H

#include "tfbase.h"
#include "bitMask.h"

enum class TFTeam : uint32_t {
  none,
  red,
  blue,
  COUNT,
};

enum class TFClass : uint32_t {
  scout,
  soldier,
  pyro,
  demo,
  hwguy,
  engineer,
  sniper,
  medic,
  spy,
  COUNT,
};

class CamBits {
public:
  enum {
    main        = 1 << 0,
    reflection  = 1 << 1,
    shadow      = 1 << 2,
  };
};

#endif // TFGLOBALS_H

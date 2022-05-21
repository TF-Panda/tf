/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfAIBase.h
 * @author brian
 * @date 2022-05-09
 */

#ifndef TFAIBASE_H
#define TFAIBASE_H

#include "pandabase.h"
#include "serverRepository.h"
#include "nodePath.h"
#include "clockObject.h"
#include "pointerTo.h"
#include "appBase.h"

/**
 *
 */
class TFAIBase : public AppBase {
public:
  TFAIBase();

  virtual bool initialize() override;
  virtual void do_frame() override;

  INLINE ServerRepository *get_air() const;
};

extern TFAIBase *simbase;

#include "tfAIBase.I"

#endif // TFAIBASE_H

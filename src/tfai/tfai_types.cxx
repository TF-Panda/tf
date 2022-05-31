/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfai_types.cxx
 * @author brian
 * @date 2022-05-12
 */

#include "tfai_types.h"
#include "serverRepository.h"
#include "distributedObjectAI.h"
#include "clientInfo.h"
#include "distributedGameAI.h"
#include "clientFrame.h"
#include "frameSnapshot.h"
#include "frameSnapshotEntry.h"
#include "packedObject.h"

/**
 *
 */
void
init_ai_types() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  ClientFrame::init_type();
  FrameSnapshot::init_type();
  FrameSnapshotEntry::init_type();
  ClientInfo::init_type();
  DistributedObjectAI::init_type();
  ServerRepository::init_type();
  PackedObject::init_type();

  DistributedGameAI::init_type();
}

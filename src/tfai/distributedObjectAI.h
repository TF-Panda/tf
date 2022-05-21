/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedObjectAI.h
 * @author brian
 * @date 2022-05-18
 */

#ifndef DISTRIBUTEDOBJECTAI_H
#define DISTRIBUTEDOBJECTAI_H

#include "tfbase.h"
#include "networkedObjectBase.h"
#include "clientInfo.h"
#include "pointerTo.h"

/**
 * Base server/AI DistributedObject view.  The only thing special about the
 * AI view is that it stores a pointer to the client that owns the object, if
 * it even has a client owner.
 */
class DistributedObjectAI : public NetworkedObjectBase {
  DECLARE_CLASS(DistributedObjectAI, NetworkedObjectBase);

public:
  DistributedObjectAI() = default;

  INLINE void set_owner(ClientInfo *owner);
  INLINE ClientInfo *get_owner() const;

protected:
  PT(ClientInfo) _owner;
};

#include "distributedObjectAI.I"

#endif // DISTRIBUTEDOBJECTAI_H

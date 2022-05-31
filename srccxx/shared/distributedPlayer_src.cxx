/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedPlayer_src.cxx
 * @author brian
 * @date 2022-05-23
 */

#include "networkClass.h"
#include "networkField.h"
#include "networkedObjectRegistry.h"

IMPLEMENT_CLASS(CLP(DistributedPlayer));

NET_CLASS_DEF_BEGIN(CLP(DistributedPlayer), CLP(DistributedEntity))
NET_CLASS_DEF_END()

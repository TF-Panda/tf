/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedPlayer.h
 * @author brian
 * @date 2022-05-23
 */

#ifndef DISTRIBUTEDPLAYER_H
#define DISTRIBUTEDPLAYER_H

#define TF_CLIENT
#include "tfbase.h"
#include "distributedEntity.h"

/**
 *
 */
class DistributedPlayer : public DistributedEntity {
  DECLARE_CLASS(DistributedPlayer, DistributedEntity);
  NET_CLASS_DECL(DistributedPlayer);
};

extern DistributedPlayer *local_avatar;

#include "distributedPlayer.I"

#endif // DISTRIBUTEDPLAYER_H

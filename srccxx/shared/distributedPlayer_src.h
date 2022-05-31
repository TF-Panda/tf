/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedPlayer_src.h
 * @author brian
 * @date 2022-05-23
 */

#include "pointerTo.h"
#include "actor.h"
#include "tfGlobals.h"

/**
 *
 */
class CLP(DistributedPlayer) : public CLP(DistributedEntity) {
  DECLARE_CLASS(CLP(DistributedPlayer), CLP(DistributedEntity));
  NET_CLASS_DECL(CLP(DistributedPlayer));

public:
  INLINE Actor *get_actor() const;
  INLINE TFClass get_class() const;

protected:
  PT(Actor) _actor;

  TFClass _class;

  bool _air_dashing;

  int _metal;
  int _max_metal;

  int _active_weapon;
  int _last_active_weapon;
};

#include "distributedPlayer_src.I"

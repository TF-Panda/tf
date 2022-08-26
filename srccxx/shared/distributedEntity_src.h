/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedEntity_src.h
 * @author brian
 * @date 2022-05-21
 */

#include "luse.h"
#include "nodePath.h"
#include "datagram.h"
#include "pointerTo.h"
#include "interpolatedVariable.h"
#include "tfGlobals.h"
#include "actor.h"

class NetworkField;

class CLP(DistributedEntity) : public CLP(DistributedObject) {
  DECLARE_CLASS(CLP(DistributedEntity), CLP(DistributedObject));
  NET_CLASS_DECL(CLP(DistributedEntity));

public:
  CLP(DistributedEntity)();

  INLINE NodePath get_node() const;

  INLINE void set_pos(const LPoint3 &pos);

#ifdef TF_CLIENT
  virtual void post_data_update(bool generate) override;
  virtual void post_interpolate() override;
#endif

  virtual void generate() override;
  virtual void announce_generate() override;
  virtual void destroy() override;

  INLINE int get_max_health() const;
  INLINE int get_health() const;
  INLINE int get_team() const;

protected:
  int _health;
  int _max_health;
  int _team;

  // Node in the scene graph that represents the entity.
  NodePath _node;

#ifdef TF_CLIENT
  PT(InterpolatedVec3) _iv_pos;
  PT(Actor) _actor;
#endif
};

#include "distributedEntity_src.I"

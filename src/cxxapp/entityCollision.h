#ifndef ENTITYCOLLISION_H
#define ENTITYCOLLISION_H

#include "collideMask.h"
#include "luse.h"
#include "gameEnums.h"

/**
 * Collision state/setup for an entity.
 */
class EntityCollision {
public:
  EntityCollision();

  bool kinematic;
  CollideShape collide_shape;
  int collide_flag;
  CollideMask from_collide_mask;
  CollideMask into_collide_mask;
  bool use_separate_trigger_mask;
  CollideMask trigger_into_mask;
  float mass;
  float damping;
  float rot_damping;
  bool trigger_callback;
  bool contact_callback;
  bool sleep_callback;
  LPoint3f hull_mins;
  LPoint3f hull_maxs;
  LVector3f trigger_fudge;

};

#endif // ENTITYCOLLISION_H

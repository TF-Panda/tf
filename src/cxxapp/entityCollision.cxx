#include "entityCollision.h"
#include "gameEnums.h"

/**
 *
 */
EntityCollision::
EntityCollision() :
  kinematic(false),
  from_collide_mask(CollideMask_world),
  into_collide_mask(CollideMask::all_on()),
  use_separate_trigger_mask(false),
  trigger_into_mask(CollideMask::all_on()),
  mass(-1),
  damping(0.0f),
  rot_damping(0.0f),
  trigger_callback(false),
  contact_callback(false),
  sleep_callback(false),
  hull_mins(0.0f),
  hull_maxs(0.0f),
  trigger_fudge(0.0f),
  collide_shape(CollideShape_empty),
  collide_flag(CollideFlag_intangible)
{
}

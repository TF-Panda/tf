/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file actor.h
 * @author brian
 * @date 2022-05-22
 */

#ifndef ACTOR_H
#define ACTOR_H

#include "tfbase.h"
#include "model.h"
#include "pointerTo.h"
#include "character.h"
#include "nodePath.h"
#include "pmap.h"

/**
 * High-level interface for animated character models.  It can be used
 * with static models too, but the animation-related methods won't do
 * anything.
 */
class EXPCL_TF_DISTRIBUTED Actor : public Model {
public:
  Actor() = default;

  INLINE static void set_global_activity_seed(unsigned int seed);
  INLINE static void clear_global_activity_seed();
  INLINE static unsigned int get_global_activity_seed();

  INLINE Character *get_character() const;
  INLINE NodePath get_character_np() const;

  INLINE bool is_animated() const;

  INLINE void joint_merge_with(Actor *parent);

  virtual bool load_model(const Filename &filename) override;
  virtual void unload_model() override;

  INLINE int get_channel_index(const std::string &name) const;

  void build_channel_name_table();

protected:
  // A global random seed used by all Actors in the world to select
  // an animation channel from an activity.  This is set during
  // client-side prediction so channel selection from activities is
  // consistent with the server.
  static unsigned int _global_activity_seed;

  // Pointer to the Character object from the loaded model.
  PT(Character) _char;
  // NodePath to the CharacterNode.
  NodePath _char_np;

  typedef pmap<std::string, int> ChannelNameTable;
  ChannelNameTable _chan_name_table;
};

#include "actor.I"

#endif // ACTOR_H

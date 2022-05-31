/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file actor.I
 * @author brian
 * @date 2022-05-22
 */

/**
 *
 */
INLINE void Actor::
set_global_activity_seed(unsigned int seed) {
  _global_activity_seed = seed;
}

/**
 *
 */
INLINE void Actor::
clear_global_activity_seed() {
  _global_activity_seed = 0u;
}

/**
 *
 */
INLINE unsigned int Actor::
get_global_activity_seed() {
  return _global_activity_seed;
}

/**
 *
 */
INLINE Character *Actor::
get_character() const {
  return _char;
}

/**
 *
 */
INLINE NodePath Actor::
get_character_np() const {
  return _char_np;
}

/**
 *
 */
INLINE bool Actor::
is_animated() const {
  return !_char.is_null();
}

/**
 *
 */
INLINE void Actor::
joint_merge_with(Actor *parent) {
  if (!is_animated() || !parent->is_animated()) {
    return;
  }
  _char->set_joint_merge_character(parent->_char);
}

/**
 * Returns the index of the animation channel with the indicated name,
 * or -1 if no such channel exists.
 */
INLINE int Actor::
get_channel_index(const std::string &name) const {
  ChannelNameTable::const_iterator it = _chan_name_table.find(name);
  if (it != _chan_name_table.end()) {
    return (*it).second;
  } else {
    return -1;
  }
}

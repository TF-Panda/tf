/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file soundEmitter.I
 * @author brian
 * @date 2022-08-24
 */

/**
 *
 */
INLINE bool SoundEmitter::SoundData::
is_empty() const {
  return _sound.is_null();
}

/**
 *
 */
INLINE bool SoundEmitter::SoundData::
is_spatialized() const {
  return !_parent.is_empty();
}

/**
 *
 */
INLINE void SoundEmitter::SoundData::
clear() {
  _sound = nullptr;
  _parent.clear();
}

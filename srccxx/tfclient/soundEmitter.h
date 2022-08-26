/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file soundEmitter.h
 * @author brian
 * @date 2022-08-24
 */

#ifndef SOUNDEMITTER_H
#define SOUNDEMITTER_H

#include "tfbase.h"
#include "audioSound.h"
#include "pointerTo.h"
#include "pvector.h"
#include "luse.h"
#include "nodePath.h"

/**
 *
 */
class SoundEmitter {
public:
  class SoundData : public ReferenceCount {
  public:
    SoundData() = default;

    PT(AudioSound) _sound;
    int _channel;

    // If not empty, sound is spatialized, positioned relative to this
    // node.
    NodePath _parent;
    LPoint3 _offset;

    std::string _event_name;

    INLINE bool is_empty() const;
    INLINE bool is_spatialized() const;
    INLINE void clear();
  };

  void register_sound(AudioSound *sound, int channel);
  void register_sound(AudioSound *sound, int channel, const NodePath &parent,
                      const LPoint3 &offset = LPoint3(0.0f));

  void insert_channel(SoundData *data);
  void stop_channel(int channel);

  void update_spatial_sounds();

private:
  pvector<PT(SoundData)> _channel_sounds;
  pvector<PT(SoundData)> _generic_sounds;
};

#include "soundEmitter.I"

#endif // SOUNDEMITTER_H

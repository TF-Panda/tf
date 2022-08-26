/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file soundEmitter.cxx
 * @author brian
 * @date 2022-08-24
 */

#include "soundEmitter.h"
#include "tfClientBase.h"

/**
 *
 */
void SoundEmitter::
register_sound(AudioSound *sound, int channel) {
  PT(SoundData) data = new SoundData;
  data->_sound = sound;
  data->_channel = channel;
  insert_channel(data);
}

/**
 *
 */
void SoundEmitter::
register_sound(AudioSound *sound, int channel, const NodePath &parent, const LPoint3 &offset) {
  PT(SoundData) data = new SoundData;
  data->_sound = sound;
  data->_channel = channel;
  data->_parent = parent;
  data->_offset = offset;

  if (!parent.is_empty()) {
    LPoint3 pos = parent.get_net_transform()->
      get_mat().xform_point(offset);
    sound->set_3d_attributes(pos[0], pos[1], pos[2], 0.0f, 0.0f, 0.0f);
  }

  insert_channel(data);
}

/**
 *
 */
void SoundEmitter::
insert_channel(SoundData *data) {
  if (data->_channel >= 0) {
    stop_channel(data->_channel);

    if (data->_channel >= _channel_sounds.size()) {
      _channel_sounds.resize(data->_channel + 1);
    }

    _channel_sounds[data->_channel] = data;

  } else {
    _generic_sounds.push_back(data);
  }

  std::ostringstream ss;
  ss << "sound-" << data << "-finished";
  data->_event_name = ss.str();
  data->_sound->set_finished_event(data->_event_name);
  cbase->get_event_handler()->add_hook(data->_event_name, handle_sound_finished, this);
}

/**
 *
 */
void SoundEmitter::
stop_channel(int channel) {
  if (channel < 0 || channel >= (int)_channel_sounds.size()) {
    return;
  }

  SoundData *data = _channel_sounds[channel];
  if (!data->_sound.is_null()) {
    data->_sound->stop();
  }
  _channel_sounds[channel] = nullptr;
}

/**
 *
 */
void SoundEmitter::
update_spatial_sounds() {
  for (SoundData *data : _channel_sounds) {
    if (data == nullptr || data->is_empty() || !data->is_spatialized()) {
      continue;
    }

    LPoint3 pos = data->_parent.get_net_transform()->
      get_mat().xform_point(data->_offset);
    data->_sound->set_3d_attributes(pos[0], pos[1], pos[2], 0.0f, 0.0f, 0.0f);
  }

  for (SoundData *data : _generic_sounds) {
    if (!data->is_spatialized()) {
      continue;
    }

    LPoint3 pos = data->_parent.get_net_transform()->
      get_mat().xform_point(data->_offset);
    data->_sound->set_3d_attributes(pos[0], pos[1], pos[2], 0.0f, 0.0f, 0.0f);
  }
}

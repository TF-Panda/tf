/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file actor.cxx
 * @author brian
 * @date 2022-05-22
 */

#include "actor.h"
#include "characterNode.h"

unsigned int Actor::_global_activity_seed = 0u;

/**
 *
 */
void Actor::
build_channel_name_table() {
  if (!is_animated()) {
    return;
  }

  for (int i = 0; i < _char->get_num_channels(); ++i) {
    _chan_name_table.insert({ _char->get_channel(i)->get_name(), i });
  }
}

/**
 *
 */
bool Actor::
load_model(const Filename &filename) {
  if (!Model::load_model(filename)) {
    return false;
  }

  _char_np = _model_np.find("**/+CharacterNode");
  if (_char_np.is_empty()) {
    _char = nullptr;
  } else {
    _char = DCAST(CharacterNode, _char_np.node())->get_character();
    build_channel_name_table();
  }

  return true;
}

/**
 *
 */
void Actor::
unload_model() {
  if (!_char_np.is_empty()) {
    _char_np.remove_node();
  }
  _char = nullptr;
  _chan_name_table.clear();
  Model::unload_model();
}

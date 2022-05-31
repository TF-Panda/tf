/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file changeFrameList.cxx
 * @author lachbr
 * @date 2020-09-13
 */

#include "changeFrameList.h"

/**
 *
 */
ChangeFrameList::
ChangeFrameList(int num_fields, int curr_tick) {
  _change_ticks.resize(num_fields);
  for (int i = 0; i < num_fields; i++) {
    _change_ticks[i] = curr_tick;
  }
}

/**
 * Sets the most recent tick that the specified fields changed.
 */
void ChangeFrameList::
set_change_tick(const int *field_indices, int num_fields, int tick) {
  for (int i = 0; i < num_fields; i++) {
    _change_ticks[field_indices[i]] = tick;
  }
}

/**
 * Builds a list of fields that changed after the specified tick.
 */
int ChangeFrameList::
get_fields_changed_after_tick(int tick, vector_int &out_fields) {

  int c = (int)_change_ticks.size();
  out_fields.reserve(c);

  for (int i = 0; i < c; i++) {
    if (_change_ticks[i] > tick) {
      out_fields.push_back(i);
    }
  }

  return (int)out_fields.size();
}

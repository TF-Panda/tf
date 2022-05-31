/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file changeFrameList.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef CHANGEFRAMELIST_H
#define CHANGEFRAMELIST_H

#include "tfbase.h"
#include "referenceCount.h"
#include "vector_int.h"

/**
 * This class holds the last tick that each state field in a distributed object
 * changed at.
 *
 * It provides fast access to a list of fields that changed within a certain
 * frame range.
 *
 * These are created once per object per frame. Since usually a very small
 * percentage of an object's fields actually change each frame, this allows you
 * to get a small set of fields to delta for each client.
 */
class ChangeFrameList : public ReferenceCount {
PUBLISHED:
  ChangeFrameList(int num_fields, int curr_tick);

  INLINE int get_num_fields() const;

  void set_change_tick(const int *field_indices, int num_fields, int tick);

  int get_fields_changed_after_tick(int tick, vector_int &out_fields);

private:
  vector_int _change_ticks;
};

#include "changeFrameList.I"

#endif // CHANGEFRAMELIST_H

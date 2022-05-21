/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshot.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef FRAMESNAPSHOT_H
#define FRAMESNAPSHOT_H

#include "tfbase.h"
#include "typedReferenceCount.h"
#include "frameSnapshotEntry.h"
#include "vector_int.h"
#include "deletedChain.h"

/**
 *
 */
class FrameSnapshot : public TypedReferenceCount {
PUBLISHED:
  ALLOC_DELETED_CHAIN(FrameSnapshot);

  INLINE FrameSnapshot(int tick_count, int num_entries);
  INLINE ~FrameSnapshot();

  INLINE void set_tick_count(int tick);
  INLINE int get_tick_count() const;

  INLINE FrameSnapshotEntry &get_entry(int n);
  INLINE int get_num_entries() const;

  INLINE void mark_entry_valid(int n);
  INLINE int get_valid_entry(int n) const;
  INLINE int get_num_valid_entries() const;

private:
  // Associated frame.
  int _tick_count;

  // State information
  FrameSnapshotEntry *_entries;
  int _num_entries;

  // This is a vector of indices into _entries that represent "valid" entries,
  // meaning objects that are seen by at least one client.
  vector_int _valid_entries;

public:
  static TypeHandle get_class_type() {
    return _type_handle;
  }
  static void init_type() {
    TypedReferenceCount::init_type();
    register_type(_type_handle, "FrameSnapshot",
                  TypedReferenceCount::get_class_type());
    }
  virtual TypeHandle get_type() const {
    return get_class_type();
  }
  virtual TypeHandle force_init_type() {init_type(); return get_class_type();}

private:
  static TypeHandle _type_handle;
};

#include "frameSnapshot.I"

#endif // FRAMESNAPSHOT_H

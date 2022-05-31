/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshot.I
 * @author lachbr
 * @date 2020-09-13
 */

/**
 *
 */
INLINE FrameSnapshot::
FrameSnapshot(int tick_count, int num_entries) {
  _tick_count = tick_count;
  _num_entries = num_entries;
  _entries = new FrameSnapshotEntry[num_entries];
}

/**
 *
 */
INLINE FrameSnapshot::
~FrameSnapshot() {
  if (_entries) {
    delete[] _entries;
    _entries = nullptr;
  }
}

/**
 *
 */
INLINE void FrameSnapshot::
set_tick_count(int tick_count) {
  _tick_count = tick_count;
}

/**
 *
 */
INLINE int FrameSnapshot::
get_tick_count() const {
  return _tick_count;
}

/**
 *
 */
INLINE FrameSnapshotEntry &FrameSnapshot::
get_entry(int n) {
  return _entries[n];
}

/**
 *
 */
INLINE int FrameSnapshot::
get_num_entries() const {
  return _num_entries;
}

/**
 *
 */
INLINE void FrameSnapshot::
mark_entry_valid(int n) {
  _valid_entries.push_back(n);
}

/**
 *
 */
INLINE int FrameSnapshot::
get_valid_entry(int n) const {
  return _valid_entries[n];
}

/**
 *
 */
INLINE int FrameSnapshot::
get_num_valid_entries() const {
  return (int)_valid_entries.size();
}

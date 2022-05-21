/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientFrame.I
 * @author lachbr
 * @date 2020-09-15
 */

/**
 *
 */
INLINE ClientFrame::
ClientFrame(FrameSnapshot *snapshot) {
  _snapshot = snapshot;
  _tick_count = snapshot->get_tick_count();
  _next = nullptr;
}

/**
 *
 */
INLINE ClientFrame::
ClientFrame(int tick_count) {
  _snapshot = nullptr;
  _tick_count = tick_count;
  _next = nullptr;
}

/**
 *
 */
INLINE ClientFrame::
ClientFrame() {
  _snapshot = nullptr;
  _tick_count = 0;
  _next = nullptr;
}

/**
 *
 */
INLINE void ClientFrame::
set_snapshot(FrameSnapshot *snapshot) {
  _snapshot = snapshot;
}

/**
 *
 */
INLINE FrameSnapshot *ClientFrame::
get_snapshot() const {
  return _snapshot;
}

/**
 *
 */
INLINE void ClientFrame::
set_tick_count(int tick_count) {
  _tick_count = tick_count;
}

/**
 *
 */
INLINE int ClientFrame::
get_tick_count() const {
  return _tick_count;
}

/**
 *
 */
INLINE void ClientFrame::
set_next(ClientFrame *next) {
  _next = next;
}

/**
 *
 */
INLINE ClientFrame *ClientFrame::
get_next() const {
  return _next;
}

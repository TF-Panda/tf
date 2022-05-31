/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientFrameManager.cxx
 * @author lachbr
 * @date 2020-09-15
 */

#include "clientFrameManager.h"

/**
 * Appends a new ClientFrame onto the list and returns the new length of the
 * list.
 */
int ClientFrameManager::
add_client_frame(ClientFrame *frame) {
  nassertr(frame->get_tick_count() > 0, 0);

  if (!_frames) {
    // First client frame
    _frames = frame;
    return 1;
  }

  ClientFrame *f = _frames;

  int count = 1;

  while (f->get_next()) {
    f = f->get_next();
    count++;
  }

  count++;
  f->set_next(frame);

  return count;
}

/**
 * Returns a ClientFrame for the specified tick number.
 *
 * If exact is true, returns the ClientFrame with the exact tick number that
 * was specified, or nullptr if no ClientFrame has that tick number.
 *
 * If exact is false, returns the ClientFrame with the exact tick number that
 * was specified, or the most recent ClientFrame before that tick number.
 */
ClientFrame *ClientFrameManager::
get_client_frame(int tick, bool exact) const {
  if (tick < 0) {
    return nullptr;
  }

  ClientFrame *frame = _frames;
  ClientFrame *last_frame = frame;

  while (frame != nullptr) {
    if (frame->get_tick_count() >= tick) {
      if (frame->get_tick_count() == tick) {
        return frame;
      }

      if (exact) {
        return nullptr;
      }

      return last_frame;
    }

    last_frame = frame;
    frame = frame->get_next();
  }

  if (exact) {
    return nullptr;
  }

  return last_frame;
}

/**
 * Removes all ClientFrames from the list before the specified tick number.
 * If tick is -1, removes all ClientFrames.
 */
void ClientFrameManager::
delete_client_frames(int tick) {
  ClientFrame *frame = _frames; // first
  ClientFrame *prev = nullptr; // last

  while (frame) {
    // remove frame if frame tick < tick
    // remove all frames if tick == -1

    if ((tick < 0) || (frame->get_tick_count() < tick)) {
      // removed frame

      if (prev) {
        prev->set_next(frame->get_next());
        frame = prev->get_next();

      } else {
        _frames = frame->get_next();
        frame = _frames;
      }

    } else {
      // go to next frame
      prev = frame;
      frame = frame->get_next();
    }
  }
}

/**
 * Returns the number of ClientFrames in the linked-list.
 */
int ClientFrameManager::
count_client_frames() const {
  int count = 0;
  ClientFrame *f = _frames;
  while (f) {
    f = f->get_next();
    count++;
  }

  return count;
}

/**
 * Removes the oldest ClientFrame in the list.
 */
void ClientFrameManager::
remove_oldest_frame() {
  ClientFrame *frame = _frames; // first

  if (!frame) {
    // had no frames
    return;
  }

  _frames = frame->get_next(); // unlink head
}

/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientFrameManager.h
 * @author lachbr
 * @date 2020-09-15
 */

#ifndef CLIENTFRAMEMANAGER_H
#define CLIENTFRAMEMANAGER_H

#include "tfbase.h"
#include "clientFrame.h"

static constexpr int max_client_frames = 128;

/**
 * This class maintains a linked-list of ClientFrames. It can return a
 * ClientFrame from a tick count. It only keeps a backlog of
 * `max_client_frames` ClientFrames.
 */
class ClientFrameManager {
PUBLISHED:
  INLINE ClientFrameManager();

  int add_client_frame(ClientFrame *frame);
  ClientFrame *get_client_frame(int tick, bool exact = true) const;
  void delete_client_frames(int tick);
  int count_client_frames() const;
  void remove_oldest_frame();

private:
  // Linked list of frames
  PT(ClientFrame) _frames;
};

#include "clientFrameManager.I"

#endif // CLIENTFRAMEMANAGER_H

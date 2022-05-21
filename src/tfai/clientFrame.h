/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientFrame.h
 * @author lachbr
 * @date 2020-09-15
 */

#ifndef CLIENTFRAME_H
#define CLIENTFRAME_H

#include "tfbase.h"
#include "frameSnapshot.h"
#include "deletedChain.h"
#include "pointerTo.h"

/**
 * This class represents a single frame of a client. It contains the snapshot
 * (state of all objects) and the tick number. This is the only class that
 * maintains a reference to the FrameSnapshot, so when there are no more
 * ClientFrames referencing the snapshot, the snapshot is freed. ClientFrames
 * are maintained in a linked-list by the ClientFrameManager class, which can
 * look up particular frames from a tick number. The ClientFrameManager class
 * only keeps a backlog of 128 ClientFrames, so when a ClientFrame is more than
 * 128 frames old, it is freed.
 */
class ClientFrame : public TypedReferenceCount {
PUBLISHED:
  ALLOC_DELETED_CHAIN(ClientFrame);

  INLINE ClientFrame(FrameSnapshot *snapshot);
  INLINE ClientFrame(int tick_count);
  INLINE ClientFrame();

  INLINE void set_snapshot(FrameSnapshot *snapshot);
  INLINE FrameSnapshot *get_snapshot() const;

  INLINE void set_tick_count(int tick_count);
  INLINE int get_tick_count() const;

  INLINE void set_next(ClientFrame *next);
  INLINE ClientFrame *get_next() const;

private:
  PT(FrameSnapshot) _snapshot;
  int _tick_count;

  PT(ClientFrame) _next;

public:
  static TypeHandle get_class_type() {
    return _type_handle;
  }
  static void init_type() {
    TypedReferenceCount::init_type();
    register_type(_type_handle, "ClientFrame",
                  TypedReferenceCount::get_class_type());
    }
  virtual TypeHandle get_type() const {
    return get_class_type();
  }
  virtual TypeHandle force_init_type() {init_type(); return get_class_type();}

private:
  static TypeHandle _type_handle;
};

#include "clientFrame.I"

#endif // CLIENTFRAME_H

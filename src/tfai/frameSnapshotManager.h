/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotManager.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef FRAMESNAPSHOTMANAGER_H
#define FRAMESNAPSHOTMANAGER_H

#include "tfbase.h"
#include "packedObject.h"
#include "pmap.h"
#include "extension.h"
#include "datagram.h"
#include "config_tfdistributed.h"

class FrameSnapshot;
class NetworkedObjectBase;

class FrameSnapshotManager {
PUBLISHED:
  INLINE FrameSnapshotManager();

  PT(PackedObject) create_packed_object(doid_t do_id);
  PackedObject *get_prev_sent_packet(doid_t do_id) const;
  void remove_prev_sent_packet(doid_t do_id);

  bool encode_object_state(NetworkedObjectBase *obj, NetworkClass *dclass, Datagram &dg,
                           PackedObject::PackedFields &fields);

  bool pack_object_in_snapshot(FrameSnapshot *snapshot, int entry, NetworkedObjectBase *obj);

  void client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot, const zoneset_t &interest);
  void client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from, FrameSnapshot *to,
                                    const zoneset_t &interest);

  PackedObject *find_or_create_object_packet_for_baseline(NetworkedObjectBase *obj);

private:
  // The most recently sent packets for each object ID.
  typedef pflat_hash_map<doid_t, PT(PackedObject), integer_hash<doid_t>> PrevSentPackets;
  PrevSentPackets _prev_sent_packets;
};

#include "frameSnapshotManager.I"

#endif // FRAMESNAPSHOTMANAGER_H

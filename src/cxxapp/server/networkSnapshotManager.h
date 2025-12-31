#ifndef NETWORKSNAPSHOTMANAGER_H
#define NETWORKSNAPSHOTMANAGER_H

#include "pandabase.h"
#include "../networkObject.h"
#include "datagram.h"
#include "vector_int.h"
#include "pta_uchar.h"
#include "pmap.h"
#include "pointerTo.h"
#include "circBuffer.h"

/**
 *
 */
struct ChangeFrameList : public ReferenceCount {
public:
  ChangeFrameList(int num_fields, int tick);
  void set_change_tick(const int *field_indices, int num_fields, int tick);
  int get_fields_changed_after_tick(int tick, vector_int &out_fields) const;

private:
  vector_int field_changes;
};

/**
 *
 */
struct PackedField {
  int field_index;
  size_t offset;
  size_t length;
};
typedef pvector<PackedField> PackedFields;

/**
 *
 */
struct PackedObject : public ReferenceCount {
  CPTA_uchar data;
  NetworkClass *net_class = nullptr;
  DO_ID do_id = 0;
  int creation_tick = 0;
  bool should_check_creation_tick = false;
  pvector<PackedField> fields;
  PT(ChangeFrameList) change_frame_list = nullptr;

  int calc_delta(const char *data, size_t length, PackedFields &fields, vector_int &delta_fields);
  void pack_datagram(Datagram &dg);
  void pack_field(Datagram &dg, int n);
};

/**
 *
 */
struct FrameSnapshotEntry {
  PT(PackedObject) packed_data = nullptr;
  bool exists = false;
  ZONE_ID zone_id = 0;
};

/**
 *
 */
struct FrameSnapshot : public ReferenceCount {
  int tick = -1;
  vector_int valid_entries;
  pvector<FrameSnapshotEntry> entries;
};

/**
 *
 */
struct ClientFrame {
  int tick = -1;
  PT(FrameSnapshot) snapshot = nullptr;
};
constexpr int max_client_frames = 128;

/**
 *
 */
struct ClientFrameList {
  CircBuffer<ClientFrame, max_client_frames> client_frames;

  int add_client_frame(const ClientFrame &frame);
  const ClientFrame *get_client_frame(int tick, bool exact = true) const;
  void remove_oldest_frame();
};

/**
 *
 */
class NetworkSnapshotManager {
public:
  PackedObject *get_prev_sent_packet(DO_ID do_id) const;
  void remove_prev_sent_packet(DO_ID do_id);

  PackedObject *get_baseline_object_state(NetworkObject *obj, NetworkClass *net_class, DO_ID do_id);
  bool pack_object_in_snapshot(FrameSnapshot *snapshot, int entry, NetworkObject *obj, DO_ID do_id, ZONE_ID zone_id, NetworkClass *net_class);

  void client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot, const pset<ZONE_ID> &interest_zones);
  void client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from, FrameSnapshot *to, const pset<ZONE_ID> &interest_zones);

private:
  bool encode_object_state(NetworkObject *obj, NetworkClass *net_class, Datagram &dg, PackedFields &fields, DO_ID do_id);

private:
  typedef pflat_hash_map<DO_ID, PT(PackedObject), integer_hash<DO_ID>> PrevSentPackets;
  PrevSentPackets _prev_sent_packets;
};

#endif // NETWORKSNAPSHOTMANAGER_H

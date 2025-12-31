#include "networkSnapshotManager.h"
#include "../networkClass.h"

/**
 *
 */
ChangeFrameList::
ChangeFrameList(int num_fields, int tick) {
  field_changes.resize(num_fields);
  for (int i = 0; i < num_fields; ++i) {
    field_changes[i] = tick;
  }
}

/**
 * Specifies that the given fields have changed at the given tick.
 */
void ChangeFrameList::
set_change_tick(const int *fields, int num_fields, int tick) {
  for (int i = 0; i < num_fields; ++i) {
    field_changes[fields[i]] = tick;
  }
}

/**
 * Returns list of field indices that changed after the given tick.
 */
int ChangeFrameList::
get_fields_changed_after_tick(int tick, vector_int &out_fields) const {
  int c = (int)field_changes.size();
  out_fields.reserve(c);

  for (int i = 0; i < c; ++i) {
    if (field_changes[i] > tick) {
      out_fields.push_back(i);
    }
  }

  return (int)out_fields.size();
}

/**
 *
 */
void PackedObject::
pack_datagram(Datagram &dg) {
  int num_fields = (int)fields.size();

  dg.add_uint16(num_fields);

  for (int i = 0; i < num_fields; ++i) {
    pack_field(dg, i);
  }
}

/**
 *
 */
void PackedObject::
pack_field(Datagram &dg, int n) {
  const PackedField &field = fields[n];
  dg.add_uint16(field.field_index);
  dg.append_data(data + field.offset, field.length);
}

/**
 *
 */
int PackedObject::
calc_delta(const char *other_data, size_t other_length, PackedFields &other_fields, vector_int &delta_fields) {
  if (fields.size() != other_fields.size()) {
    return -1;
  }

  if (data.size() == 0 || other_length == 0) {
    return -1; // Treat all fields as changed.
  }

  int num_fields = (int)fields.size();

  delta_fields.reserve(num_fields);

  for (int i = 0; i < num_fields; ++i) {
    const PackedField &field = fields[i];
    const PackedField &other_field = other_fields[i];

    if (field.length != other_field.length) {
      // If the packed field length is different, obviously the value
      // is different.
      delta_fields.push_back(i);

    } else if (memcmp(data.p() + field.offset, other_data + other_field.offset, field.length)) {
      // Actual bits are different.
      // TODO: Handle floats!
      delta_fields.push_back(i);
    }
  }

  return (int)delta_fields.size();
}

/**
 *
 */
int ClientFrameList::
add_client_frame(const ClientFrame &frame) {
  nassertr(frame.snapshot != nullptr && frame.tick >= 0, (int)client_frames.size());

  if (client_frames.full()) {
    // Adding this frame would give us too many, so get rid of the
    // oldest one (the one at the front of the list).
    remove_oldest_frame();
  }
  client_frames.push_back(frame);

  return (int)client_frames.size();
}

/**
 *
 */
void ClientFrameList::
remove_oldest_frame() {
  client_frames.pop_front();
}

/**
 * Returns the client frame for the given tick.  If exact is true,
 * it tries to find the frame with that exact tick, and returns nullptr
 * if we don't have a frame for that tick.  If exact is false, it will
 * return the most recent frame before the tick if there's no frame for
 * the exact tick.
 */
const ClientFrame *ClientFrameList::
get_client_frame(int tick, bool exact) const {
  if (tick < 0) {
    return nullptr;
  }

  for (size_t i = 0; i < client_frames.size(); ++i) {
    const ClientFrame *frame = &client_frames[i];
    if (frame->tick >= tick) {
      if (frame->tick == tick) {
	return frame;
      }

      if (exact) {
	return nullptr;
      }

      if (i == 0) {
	return &client_frames.front();
      } else {
	return &client_frames[i - 1];
      }
    }
  }

  if (exact) {
    return nullptr;
  }

  return &client_frames.back();
}

/**
 *
 */
PackedObject *NetworkSnapshotManager::
get_prev_sent_packet(DO_ID do_id) const {
  auto it = _prev_sent_packets.find(do_id);
  if (it != _prev_sent_packets.end()) {
    return (*it).second;
  }
  return nullptr;
}

/**
 *
 */
void NetworkSnapshotManager::
remove_prev_sent_packet(DO_ID do_id) {
  auto it = _prev_sent_packets.find(do_id);
  if (it != _prev_sent_packets.end()) {
    _prev_sent_packets.erase(it);
  }
}

/**
 *
 */
PackedObject *NetworkSnapshotManager::
get_baseline_object_state(NetworkObject *obj, NetworkClass *net_class, DO_ID do_id) {
  PackedObject *prev = get_prev_sent_packet(do_id);
  if (prev != nullptr) {
    // We had a previously sent packet, use that.
    return prev;
  }

  // Never sent a packet for this object.
  // Pack initial state and store that as the most recently sent packet for the object.
  Datagram dg;
  PackedFields fields;
  if (!encode_object_state(obj, net_class, dg, fields, do_id)) {
    return nullptr;
  }

  // Use a bogus -1 tick count so any fields that don't change between now and when
  // the snapshot is built don't get sent again.
  PT(ChangeFrameList) change_frame = new ChangeFrameList((int)fields.size(), -1);

  CPTA_uchar data = dg.get_array();
  PT(PackedObject) pack = new PackedObject;
  pack->change_frame_list = change_frame;
  pack->do_id = do_id;
  pack->net_class = net_class;
  pack->creation_tick = -1;
  pack->data = data;
  pack->fields = std::move(fields);
  _prev_sent_packets.insert({ do_id, pack });
  return pack;
}

/**
 *
 */
bool NetworkSnapshotManager::
encode_object_state(NetworkObject *obj, NetworkClass *net_class, Datagram &dg, PackedFields &fields, DO_ID do_id) {
  int num_fields = net_class->get_num_inherited_fields();
  fields.reserve(num_fields);

  size_t prev_length;
  size_t pos = 0;
  for (int i = 0; i < num_fields; ++i) {
    NetworkField *field = net_class->get_inherited_field(i);
    if (field == nullptr) {
      continue;
    }

    prev_length = dg.get_length();
    field->write(obj, dg);
    size_t bytes_written = dg.get_length() - prev_length;

    // Store the location and length of the field in the overall buffer.
    fields.push_back({ i, pos, bytes_written });
    pos += bytes_written;
  }

  return true;
}

/**
 *
 */
bool NetworkSnapshotManager::
pack_object_in_snapshot(FrameSnapshot *snapshot, int entry_idx, NetworkObject *obj,
			DO_ID do_id, ZONE_ID zone_id, NetworkClass *net_class) {
  nassertr(entry_idx >= 0 && entry_idx < snapshot->entries.size(), false);
  FrameSnapshotEntry &entry = snapshot->entries[entry_idx];
  entry.exists = true;
  entry.zone_id = zone_id;
  snapshot->valid_entries.push_back(entry_idx);

  // Encode full state of object.
  Datagram dg;
  PackedFields packed_fields;
  if (!encode_object_state(obj, net_class, dg, packed_fields, do_id)) {
    return false;
  }

  // Grab packed data from the Datagram.
  CPTA_uchar data = dg.get_array();

  PT(ChangeFrameList) change_frame = nullptr;

  PackedObject *prev_pack = get_prev_sent_packet(do_id);
  if (prev_pack != nullptr) {
    // We have a previously sent packet for this object.  Calculate a delta
    // between the state we just packed and this previous state.

    vector_int delta_params;
    int changes = prev_pack->calc_delta((const char *)data.p(), data.size(), packed_fields, delta_params);

    if (changes == 0) {
      // If there are no changes between the previous state and the current state,
      // just use the previous state.
      entry.packed_data = prev_pack;
      return true;
    }

    // -1 means we can't calculate a delta and all fields should be treated as changed.
    if (changes != -1) {
      // We have changed fields.  Move the ChangeFrameList from the previous packet
      // to our new one, and note the ticks of fields that changed in this packet,
      // leaving fields that didn't change at their last tick.

      change_frame = prev_pack->change_frame_list;
      prev_pack->change_frame_list = nullptr;
      if (change_frame != nullptr) {
	// Record the deltas if the prev pack had a change list.
	change_frame->set_change_tick(delta_params.data(), changes, snapshot->tick);
      }
    }
  }

  if (change_frame == nullptr) {
    // We have never sent a packet for this object or the prev pack didn't
    // have a change list.
    change_frame = new ChangeFrameList((int)packed_fields.size(), snapshot->tick);
  }

  // Now make a PackedObject and store the new packed data in there.
  PT(PackedObject) pack = new PackedObject;
  pack->data = data;
  pack->net_class = net_class;
  pack->do_id = do_id;
  pack->creation_tick = snapshot->tick;
  pack->fields = std::move(packed_fields);
  pack->change_frame_list = change_frame;
  // Note this as the most recent packet for this object.
  _prev_sent_packets.insert({ do_id, pack });

  entry.packed_data = pack;

  return true;
}

/**
 *
 */
void NetworkSnapshotManager::
client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot, const pset<ZONE_ID> &interest_zones) {
  // Record tick count of the snapshot.
  dg.add_uint32(snapshot->tick);
  // Indicated this is *not* a delta snapshot.
  dg.add_bool(false);

  // Write the objects.
  int num_objects = 0;
  Datagram object_dg;
  for (int i = 0; i < snapshot->valid_entries.size(); ++i) {
    const FrameSnapshotEntry &entry = snapshot->entries[snapshot->valid_entries[i]];
    if (interest_zones.find(entry.zone_id) == interest_zones.end()) {
      // Object not seen by this client, don't include in snapshot.
      continue;
    }

    // Object ID
    object_dg.add_uint32(entry.packed_data->do_id);

    // This is not a delta snapshot, so just copy the absolute state.
    entry.packed_data->pack_datagram(object_dg);

    ++num_objects;
  }

  // # of objects in this client snapshot.
  dg.add_uint16(num_objects);

  // Copy object data onto main datagram.
  dg.append_data(object_dg.get_data(), object_dg.get_length());
}

/**
 *
 */
void NetworkSnapshotManager::
client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from, FrameSnapshot *to, const pset<ZONE_ID> &interest_zones) {
  // Record tick count of the snapshot.
  dg.add_uint32(to->tick);
  // Indicate this is a delta snapshot.
  dg.add_bool(true);

  int num_objects = 0;
  Datagram object_dg;

  vector_int changed_fields;

  for (int i = 0; i < to->valid_entries.size(); ++i) {
    const FrameSnapshotEntry &entry = to->entries[to->valid_entries[i]];
    if (interest_zones.find(entry.zone_id) == interest_zones.end()) {
      // Object not in client interest zones.
      continue;
    }

    PackedObject *packet = entry.packed_data;

    int num_changes = -1;
    if (packet->change_frame_list != nullptr) {
      changed_fields.clear();
      // Figure out which fields to send for the object.
      // Just the ones that changes from the old snapshot to the new one.
      num_changes = packet->change_frame_list->get_fields_changed_after_tick(from->tick, changed_fields);
    }

    if (num_changes == 0) {
      // Nothing changed, don't send anything.
      continue;
    }

    // Object ID
    object_dg.add_uint32(packet->do_id);

    if (num_changes != -1) {
      // How many fields are there?
      object_dg.add_uint16(num_changes);

      // Now copy each changed field into the datagram.
      for (int j = 0; j < num_changes; ++j) {
	packet->pack_field(dg, changed_fields[j]);
      }
    } else {
      // -1 means all fields changed, so just pack the whole object.
      packet->pack_datagram(dg);
    }

    ++num_changes;
  }

  // # of objects in this client snapshot.
  dg.add_uint16(num_objects);

  // Copy object data onto the main datagram.
  dg.append_data(object_dg.get_data(), object_dg.get_length());
}

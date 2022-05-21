/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotManager.cxx
 * @author lachbr
 * @date 2020-09-13
 */

#include "frameSnapshotManager.h"
#include "frameSnapshot.h"
#include "networkClass.h"
#include "networkField.h"
#include "networkedObjectBase.h"
#include "datagram.h"

/**
 * Creates and returns a new PackedObject for the specified object ID.
 */
PT(PackedObject) FrameSnapshotManager::
create_packed_object(doid_t do_id) {
  PT(PackedObject) obj = new PackedObject;
  obj->set_do_id(do_id);
  _prev_sent_packets[do_id] = obj;
  return obj;
}

/**
 * Returns the most recently sent packed state for the specified object ID, or
 * nullptr if no packet was ever sent for the object.
 */
PackedObject *FrameSnapshotManager::
get_prev_sent_packet(doid_t do_id) const {
  auto itr = _prev_sent_packets.find(do_id);
  if (itr != _prev_sent_packets.end()) {
    return itr->second;
  }

  return nullptr;
}

/**
 * Removes the most recently packed state for the specified object ID from the
 * cache. Call this when the object is being deleted so that a possible future
 * object with the same ID does not use this state!
 */
void FrameSnapshotManager::
remove_prev_sent_packet(doid_t do_id) {
  auto itr = _prev_sent_packets.find(do_id);
  if (itr != _prev_sent_packets.end()) {
    _prev_sent_packets.erase(itr);
  }
}

/**
 *
 */
bool FrameSnapshotManager::
encode_object_state(NetworkedObjectBase *obj, NetworkClass *dclass, Datagram &dg,
                    PackedObject::PackedFields &fields) {
  size_t num_fields = dclass->get_num_fields();
  fields.reserve(num_fields);

  // Pack all fields into the datagram, recording the offset and length of
  // each serialized field.
  size_t prev_length;
  size_t pos = 0;
  for (size_t i = 0; i < num_fields; ++i) {
    NetworkField *field = dclass->get_field(i);
    size_t prev_length = dg.get_length();
    field->serialize(dg, (const unsigned char *)obj);

    // Determine how many bytes were just written for this field.
    size_t field_length = dg.get_length() - prev_length;

    // Store the location and length of the field in the state Datagram.
    fields.push_back({ dclass, (int)i, pos, field_length });
    pos += field_length;
  }

  return true;
}

/**
 *
 */
bool FrameSnapshotManager::
pack_object_in_snapshot(FrameSnapshot *snapshot, int entry_idx, NetworkedObjectBase *obj) {
  NetworkClass *dclass = obj->get_network_class();
  doid_t do_id = obj->get_network_id();

  FrameSnapshotEntry &entry = snapshot->get_entry(entry_idx);
  entry.set_class(dclass);
  entry.set_do_id(do_id);
  entry.set_zone_id(obj->get_zone_id());
  entry.set_exists(true);

  snapshot->mark_entry_valid(entry_idx);

  //
  // First encode the object's state data.
  //

  Datagram dg;
  PackedObject::PackedFields packed_fields;
  if (!encode_object_state(obj, dclass, dg, packed_fields)) {
    return false;
  }

  // Get byte array from the Datagram.
  CPTA_uchar data = dg.get_array();

  PT(ChangeFrameList) change_frame = nullptr;

  // If this object was previously in there, then it should have a valid
  // ChangeFrameList which we can delta against to figure out which fields
  // have changed.
  //
  // If not, then we want to set up a new ChangeFrameList.

  PackedObject *prev_pack = get_prev_sent_packet(do_id);
  if (prev_pack != nullptr) {
    // We have a previously sent packet for this object.  Calculate a delta
    // between the state we just packed and this previous state.

    vector_int delta_params;
    int changes = prev_pack->calc_delta(data, packed_fields, delta_params);

    if (tfdistributed_cat.is_debug()) {
      tfdistributed_cat.debug()
        << changes << " field memory changes on object " << do_id << " from tick "
        << prev_pack->get_snapshot_creation_tick() << " to "
        << snapshot->get_tick_count() << "\n";
    }

    if (changes == 0) {
      // If there are no changes between the previous state and the current
      // state, just use the previous state.
      entry.set_packed_object(prev_pack);
      return true;
    }

    // -1 means we can't calculate a delta and all fields should be treated as
    // changed.
    if (changes != -1) {
      // We have changed fields. Snag the ChangeFrameList from the previous
      // packet to store on our new packet.

      // Snag it
      change_frame = prev_pack->take_change_frame_list();
      if (change_frame != nullptr) {
        if (tfdistributed_cat.is_debug()) {
          tfdistributed_cat.debug()
            << "Setting " << changes << " changed fields on tick " << snapshot->get_tick_count() << " doId " << do_id << "\n";
        }
        // Record the deltas if the prev pack had a change list
        change_frame->set_change_tick(delta_params.data(), changes, snapshot->get_tick_count());
      }
    }
  }

  if (change_frame == nullptr) {
    // We have never sent a packet for this object or the prev pack didn't
    // have a change list.
    change_frame = new ChangeFrameList((int)packed_fields.size(), snapshot->get_tick_count());
  }

  // Now make a PackedObject and store the new packed data in there.
  PT(PackedObject) packed_object = create_packed_object(do_id);
  packed_object->set_change_frame_list(change_frame);
  packed_object->set_class(dclass);
  packed_object->set_snapshot_creation_tick(snapshot->get_tick_count());
  packed_object->set_array(std::move(data));
  packed_object->set_fields(std::move(packed_fields));

  entry.set_packed_object(packed_object);

  return true;
}

/**
 * Builds a datagram out of the specified snapshot suitable for sending to a
 * client.  Only objects that are in the specified interest zones are packed
 * into the datagram.
 */
void FrameSnapshotManager::
client_format_snapshot(Datagram &dg, FrameSnapshot *snapshot,
                       const zoneset_t &interest) {

  // Record tick count of the snapshot.
  dg.add_uint32(snapshot->get_tick_count());

  // Indicate this is *not* a delta snapshot.
  dg.add_uint8(0);

  int num_objects = 0;
  Datagram object_dg;
  for (int i = 0; i < snapshot->get_num_valid_entries(); i++) {
    FrameSnapshotEntry &entry = snapshot->get_entry(snapshot->get_valid_entry(i));
    //if (interest.find(entry.get_zone_id()) == interest.end()) {
      // Object not seen by this client, don't include in client snapshot.
    //  continue;
    //}

    // Object ID
    object_dg.add_uint32(entry.get_do_id());

    // This is not a delta snapshot, just copy the absolute state
    // onto the datagram.
    PackedObject *packet = entry.get_packed_object();
    packet->pack_datagram(object_dg);

    num_objects++;
  }

  // # of objects in this client snapshot.
  dg.add_uint16(num_objects);

  // Copy object data onto main datagram.
  dg.append_data(object_dg.get_data(), object_dg.get_length());
}

/**
 * Builds a datagram out of the specified snapshot suitable for sending to a
 * client.  Only objects that are in the specified interest zones are packed
 * into the datagram, and only fields that have changed between `from` and `to`
 * are packed.
 */
void FrameSnapshotManager::
client_format_delta_snapshot(Datagram &dg, FrameSnapshot *from, FrameSnapshot *to,
                             const zoneset_t &interest) {

  // Record tick count of the snapshot.
  dg.add_uint32(to->get_tick_count());

  // Indicate this is a delta snapshot.
  dg.add_uint8(1);

  int num_objects = 0;
  Datagram object_dg;
  for (int i = 0; i < to->get_num_valid_entries(); i++) {
    FrameSnapshotEntry &entry = to->get_entry(to->get_valid_entry(i));
    //if (interest.find(entry.get_zone_id()) == interest.end()) {
    //  // Object not seen by this client, don't include in client snapshot
    //  continue;
    //}

    PackedObject *packet = entry.get_packed_object();

    vector_int changed_fields;
    int num_changes = packet->get_fields_changed_after_tick(from->get_tick_count(), changed_fields);

    if (tfdistributed_cat.is_debug()) {
      tfdistributed_cat.debug()
        << from->get_tick_count() << " to " << to->get_tick_count() << " for client\n";
      tfdistributed_cat.debug()
        << num_changes << " fields changed for client after tick " << from->get_tick_count() << " doId " << packet->get_do_id() << "\n";
    }

    if (num_changes == 0) {
      // Nothing changed from previous client snapshot, don't include this
      // object.
      continue;
    }

    // Object ID
    object_dg.add_uint32(entry.get_do_id());

    if (num_changes != -1) {
      // How many fields are there?
      object_dg.add_uint16(num_changes);

      // Now copy each changed field into the datagram
      for (int j = 0; j < num_changes; j++) {
        packet->pack_field(object_dg, changed_fields[j]);
      }

    } else {
      // -1 means all fields changed, so just pack the whole object
      packet->pack_datagram(object_dg);
    }

    num_objects++;
  }

  // # of objects in this client snapshot
  dg.add_uint16(num_objects);

  // Copy object data onto main datagram
  dg.append_data(object_dg.get_data(), object_dg.get_length());
}

/**
 *
 */
PackedObject *FrameSnapshotManager::
find_or_create_object_packet_for_baseline(NetworkedObjectBase *obj) {
  NetworkClass *dclass = obj->get_network_class();
  doid_t do_id = obj->get_network_id();

  PackedObject *prev_pack = get_prev_sent_packet(do_id);
  if (prev_pack) {
    // We had a previously sent packet, use that.
    return prev_pack;
  }

  // We never sent a packet for this object, it must be brand new.
  // Pack the initial state into a new PackedObject and store that as the most
  // recently sent packet for the object.

  Datagram packer;
  PackedObject::PackedFields fields;
  if (!encode_object_state(obj, dclass, packer, fields)) {
    return nullptr;
  }

  CPTA_uchar data = packer.get_array();

  // Use a bogus -1 tick count so any fields that don't change between now and when
  // the snapshot is built don't get sent again.
  PT(ChangeFrameList) change_frame = new ChangeFrameList((int)fields.size(), -1);

  PT(PackedObject) pack = create_packed_object(do_id);
  pack->set_change_frame_list(change_frame);
  pack->set_class(dclass);
  pack->set_snapshot_creation_tick(-1);
  pack->set_array(std::move(data));
  pack->set_fields(std::move(fields));

  return pack;
}

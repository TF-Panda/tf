/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file frameSnapshotEntry.h
 * @author lachbr
 * @date 2020-09-13
 */

#ifndef FRAMESNAPSHOTENTRY_H
#define FRAMESNAPSHOTENTRY_H

#include "tfbase.h"
#include "deletedChain.h"
#include "typedObject.h"
#include "config_tfdistributed.h"

class NetworkClass;
class PackedObject;

/**
 * Individual object data, did the object exist and what was its object id.
 * Also stores a handle to the absolute state of the object at the time of the
 * snapshot.
 */
class FrameSnapshotEntry : public TypedObject {
PUBLISHED:
  ALLOC_DELETED_CHAIN(FrameSnapshotEntry);

  INLINE FrameSnapshotEntry();

  INLINE void set_class(NetworkClass *dclass);
  INLINE NetworkClass *get_class() const;

  INLINE void set_do_id(doid_t do_id);
  INLINE doid_t get_do_id() const;

  INLINE void set_zone_id(zoneid_t zone_id);
  INLINE zoneid_t get_zone_id() const;

  INLINE void set_exists(bool exists);
  INLINE bool get_exists() const;

  INLINE void set_packed_object(PackedObject *obj);
  INLINE PackedObject *get_packed_object() const;

private:
  NetworkClass *_dclass;
  doid_t _do_id;
  zoneid_t _zone_id;
  bool _exists;
  PackedObject *_packed_data;

public:
  static TypeHandle get_class_type() {
    return _type_handle;
  }
  static void init_type() {
    TypedObject::init_type();
    register_type(_type_handle, "FrameSnapshotEntry",
                  TypedObject::get_class_type());
    }
  virtual TypeHandle get_type() const {
    return get_class_type();
  }
  virtual TypeHandle force_init_type() {init_type(); return get_class_type();}

private:
  static TypeHandle _type_handle;
};

#include "frameSnapshotEntry.I"

#endif // FRAMESNAPSHOTENTRY_H

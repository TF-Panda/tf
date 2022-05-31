/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkRepository.h
 * @author brian
 * @date 2022-05-05
 */

#ifndef NETWORKREPOSITORY_H
#define NETWORKREPOSITORY_H

#include "tfbase.h"
#include "typedReferenceCount.h"
#include "pmap.h"
#include "networkedObjectBase.h"
#include "pointerTo.h"
#include "stl_compares.h"

/**
 *
 */
class EXPCL_TF_DISTRIBUTED NetworkRepository : public TypedReferenceCount {
  DECLARE_CLASS(NetworkRepository, TypedReferenceCount);

public:
  NetworkRepository() = default;

  INLINE NetworkedObjectBase *get_object(uint32_t id) const;
  INLINE bool has_object(uint32_t id) const;

protected:
  // This table stores all of the alive networked objects in the game.
  // The objects are mapped by their network IDs.
  typedef pflat_hash_map<uint32_t, PT(NetworkedObjectBase), integer_hash<uint32_t>> ObjectTable;
  ObjectTable _net_obj_table;
};

#include "networkRepository.I"

#endif // NETWORKREPOSITORY_H

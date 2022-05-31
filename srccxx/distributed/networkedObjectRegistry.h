/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkedObjectRegistry.h
 * @author brian
 * @date 2022-05-05
 */

#ifndef NETWORKEDOBJECTREGISTRY_H
#define NETWORKEDOBJECTREGISTRY_H

#include "tfbase.h"
#include "pmap.h"
#include "typeHandle.h"
#include "memoryBase.h"
#include "ordered_vector.h"

class NetworkedObjectProxy;
class NetworkClass;

/**
 * A global class that maintains a registry of all the networked classes in
 * the universe.
 */
class EXPCL_TF_DISTRIBUTED NetworkedObjectRegistry : public MemoryBase {
public:
  INLINE static NetworkedObjectRegistry *get_global_ptr();

  void register_class(NetworkClass *cls);
  void sort_classes();

  INLINE size_t get_num_classes() const;
  INLINE NetworkClass *get_class(size_t n) const;

  size_t get_hash() const;

  void output(std::ostream &out) const;

private:
  static NetworkedObjectRegistry *_global_ptr;

  typedef pmap<std::string, NetworkClass *> ClassesByName;
  ClassesByName _classes_by_name;

  // Classes sorted by ID.
  typedef ordered_vector<NetworkClass *, indirect_less<NetworkClass *>> OrderedClasses;
  OrderedClasses _ordered_classes;
};

#include "networkedObjectRegistry.I"

#endif // NETWORKEDOBJECTREGISTRY_H

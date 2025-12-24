/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file entityFactory.cxx
 * @author brian
 * @date 2024-09-01
 */

#include "entityFactory.h"

EntityFactory *EntityFactory::_global_ptr = nullptr;

/**
 *
 */
void EntityFactory::
register_entity(const std::string &classname, CreationFunc *factory) {
  _mapping[classname] = factory;
}

/**
 * Creates and returns a new instance of the entity type with the given class name.
 * Returns nullptr if no entity has that class name.
 */
Entity *EntityFactory::
create_entity(const std::string &classname) {
  int itr = _mapping.find(classname);
  if (itr == -1) {
    return nullptr;
  }
  CreationFunc *factory = _mapping.get_data(itr);
  return (*factory)();
}

/**
 *
 */
EntityFactory *EntityFactory::
get_global_ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new EntityFactory;
  }
  return _global_ptr;
}

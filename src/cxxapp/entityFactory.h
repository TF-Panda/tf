/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file entityFactory.h
 * @author brian
 * @date 2024-09-01
 */

#ifndef ENTITYFACTORY_H
#define ENTITYFACTORY_H

#include "simpleHashMap.h"

class Entity;

/**
 * Maintains a mapping of entity class names to functions to create them,
 * so we can create entities by class name alone.
 */
class EntityFactory {
public:
  typedef Entity *(CreationFunc)();

  void register_entity(const std::string &classname, CreationFunc *factory);
  Entity *create_entity(const std::string &classname);

  static EntityFactory *get_global_ptr();

private:
  SimpleHashMap<std::string, CreationFunc *, string_hash> _mapping;

private:
  static EntityFactory *_global_ptr;
};

#include "entityFactory.I"

#endif // ENTITYFACTORY_H

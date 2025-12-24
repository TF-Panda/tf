/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file entity.cxx
 * @author brian
 * @date 2024-08-31
 */

#include "entity.h"
#include "networkClass.h"
#include "vectorNetClasses.h"

TypeHandle Entity::_type_handle;
NetworkClass *Entity::_network_class = nullptr;

/**
 *
 */
Entity::
Entity(const std::string &name) :
  PandaNode("entity-" + name),
  _health(100),
  _max_health(100)
{
}

/**
 *
 */
void Entity::
spawn() {
  _self_path = NodePath(this);
}

/**
 *
 */
void Entity::
destroy() {
  _self_path.clear();

  // Detach from all parents in graph (most likely just one).
  PandaNode::Parents parents = get_parents();
  for (int i = 0; i < parents.get_num_parents(); ++i) {
    parents.get_parent(i)->remove_child(this);
  }
}

static void test_fetch_pos(void *object, void *dest) {
  Entity *e = (Entity *)object;
  LPoint3f pos = e->get_transform()->get_pos();
  *(LPoint3f *)dest = pos;
}

static void test_write_pos(void *object, void *data) {
  LPoint3f pos = *(LPoint3f *)data;
  Entity *e = (Entity *)object;
  e->set_transform(e->get_transform()->set_pos(pos));
}

void Entity::
init_network_class() {
  BEGIN_NETWORK_CLASS_NOBASE(Entity)

    MAKE_NET_FIELD(Entity, _health, NetworkField::DT_int16)
    MAKE_NET_FIELD(Entity, _max_health, NetworkField::DT_int16)
    MAKE_STRUCT_NET_FIELD(Entity, _test_pos, Position_NetClass)
    MAKE_INDIRECT_STRUCT_NET_FIELD(LPoint3f, pos, Position_NetClass, test_fetch_pos, test_write_pos)

  END_NETWORK_CLASS()
}

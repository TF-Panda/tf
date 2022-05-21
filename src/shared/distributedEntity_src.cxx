/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedEntity_src.cxx
 * @author brian
 * @date 2022-05-21
 */

#include "networkedObjectRegistry.h"
#include "networkClass.h"
#include "networkedObjectBase.h"
#include "networkField.h"
#include "appBase.h"
#include "loader.h"

#ifdef TF_CLIENT
#include "tfGlobals.h"
#include "mapLightingEffect.h"
#endif

IMPLEMENT_CLASS(CLP(DistributedEntity));

NET_CLASS_DEF_BEGIN_NOBASE(CLP(DistributedEntity))
  _network_class->add_field(
    new NetworkField("health", NET_OFFSET(CLP(DistributedEntity), _health),
                     NetworkField::NDT_int, NetworkField::DT_int16)
  );
  _network_class->add_field(
    new NetworkField("max_health", NET_OFFSET(CLP(DistributedEntity), _max_health),
                     NetworkField::NDT_int, NetworkField::DT_int16)
  );
  _network_class->add_field(
    new NetworkField("team", NET_OFFSET(CLP(DistributedEntity), _team),
                     NetworkField::NDT_int, NetworkField::DT_uint8)
  );
  _network_class->add_field(
    new NetworkField("pos", NET_OFFSET(CLP(DistributedEntity), _pos),
                     NetworkField::NDT_vec3, NetworkField::DT_int32, 1, 100)
  );

NET_CLASS_DEF_END()

/**
 *
 */
CLP(DistributedEntity)::
CLP(DistributedEntity)() :
  _node("entity"),
  _health(100),
  _max_health(100),
  _gravity(1.0f),
  _team(-1) {
#ifdef TF_CLIENT
  _node.set_effect(MapLightingEffect::make(CamBits::main));
  _node.show_through(CamBits::shadow);
  Loader *loader = Loader::get_global_ptr();
  NodePath mdl = NodePath(loader->load_sync("models/misc/smiley"));
  mdl.reparent_to(_node);
  _iv_pos = new InterpolatedVec3;
  add_interpolated_var(_iv_pos, &_pos, "iv_pos");
#endif
}

#ifdef TF_CLIENT
/**
 *
 */
void DistributedEntity::
post_data_update(bool generate) {
  DistributedObject::post_data_update(generate);
  _node.set_pos(_pos);
}

/**
 *
 */
void DistributedEntity::
post_interpolate() {
  DistributedObject::post_interpolate();
  _node.set_pos(_pos);
}
#endif

/**
 *
 */
void CLP(DistributedEntity)::
announce_generate() {
  CLP(DistributedObject)::announce_generate();
  _node.reparent_to(base->get_render());
}

/**
 *
 */
void CLP(DistributedEntity)::
destroy() {
  if (!_node.is_empty()) {
    _node.remove_node();
  }
  CLP(DistributedObject)::destroy();
}

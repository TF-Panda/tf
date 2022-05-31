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
#include "actor.h"
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
                     NetworkField::NDT_uint, NetworkField::DT_uint8)
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
  _team(TFTeam::none) {
#ifdef TF_CLIENT
  // Make the node compute its lighting state from the lighting
  // information in the level when it's rendered.
  _node.set_effect(MapLightingEffect::make(CamBits::main));
  // And render into shadow maps.
  _node.show_through(CamBits::shadow);
  // We don't need to consider culling past the root of the entity
  // node.  Entities should be treated as single culling units.
  _node.node()->set_final(true);
  // Link the node back to the entity.
  _node.set_user_data(this);

  _actor = new Actor;
  _actor->load_model("models/char/engineer");
  _actor->get_character()->loop(_actor->get_channel_index("a_runSW_PRIMARY"), true);
  _actor->get_model_np().reparent_to(_node);

  // Add interpolators for transform state of the entity.
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
generate() {
  CLP(DistributedObject)::generate();
  // Make the node for this entity recognizable.  Assign the top-level
  // class name followed by the doId.
  _node.set_name(unique_name(get_type().get_name()));
}

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
#ifdef TF_CLIENT
  _actor->unload_model();
#endif
  if (!_node.is_empty()) {
    _node.remove_node();
  }
  CLP(DistributedObject)::destroy();
}

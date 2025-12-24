/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file world.cxx
 * @author brian
 * @date 2024-09-01
 */

#include "world.h"
#include "globals.h"
#include "mapData.h"
#include "physTriangleMeshData.h"
#include "physTriangleMesh.h"
#include "physMaterial.h"
#include "physShape.h"
#include "physRigidStaticNode.h"
#include "nodePath.h"
#include "geomNode.h"

TypeHandle World::_type_handle;

/**
 *
 */
World::
World() :
  Entity("world"),
  _model_index(0)
{
}

/**
 *
 */
void World::
spawn() {
  globals->world = this;

  Entity::spawn();

  _map_model = globals->map_data->get_model(_model_index);
  init_world_collisions();
  parent_model_geometry();

  get_node_path().reparent_to(globals->render);
}

/**
 * Parent's the level geometry associated with this entity to the entity itself,
 * so it appears in the scene.
 */
void World::
parent_model_geometry() {
  GeomNode *gn = _map_model->get_geom_node();
  if (gn != nullptr) {
    NodePath np(gn->make_copy());
    np.flatten_light();
    np.reparent_to(get_node_path());
  }
}

/**
 *
 */
void World::
init_world_collisions() {
  // Load collisions from world map data.

  for (int i = 0; i < _map_model->get_num_tri_groups(); ++i) {
    const MapModel::CollisionGroup *group = _map_model->get_tri_group(i);
    PhysTriangleMesh tri_mesh(new PhysTriangleMeshData(group->get_tri_mesh_data()));
    pvector<PT(PhysMaterial)> materials;
    for (int j = 0; j < group->get_num_surface_props(); ++j) {
      // TODO: Get physics material from surface prop.
      materials.push_back(new PhysMaterial(0.3f, 0.3f, 0.3f));
    }

    assert(materials.size() > 0u);

    PT(PhysShape) shape = new PhysShape(tri_mesh, materials[0]);
    shape->set_scene_query_shape(true);
    shape->set_simulation_shape(true);
    shape->set_trigger_shape(false);

    if (materials.size() > 1u) {
      for (size_t j = 1u; j < materials.size(); ++j) {
        shape->add_material(materials[i]);
      }
      shape->submit_materials();
    }

    PT(PhysRigidStaticNode) body = new PhysRigidStaticNode("world-collide-" + group->get_collide_type());
    body->set_from_collide_mask(CG_world); // TODO base it upon the collide type name.
    body->add_shape(shape);
    body->add_to_scene(globals->physics_world);
    body->set_user_data(this);

    // Put it under our entity node in the SG.
    get_node_path().attach_new_node(body);

    _world_collisions.push_back(body);
  }
}

/**
 *
 */
void World::
destroy() {
  // Tear down the static world collisions.
  for (PhysRigidStaticNode *body : _world_collisions) {
    body->remove_from_scene(globals->physics_world);
  }
  _world_collisions.clear();
  globals->world = nullptr;

  Entity::destroy();
}

/**
 *
 */
Entity *World::
create_World() {
  return new World;
}

/**
 *
 */
void World::
register_ent_factory()  {
  EntityFactory::get_global_ptr()->register_entity("worldspawn", create_World);
}

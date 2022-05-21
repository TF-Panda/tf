/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file gameLevel_src.cxx
 * @author brian
 * @date 2022-05-19
 */

#include "pdxElement.h"
#include "loader.h"
#include "modelRoot.h"
#include "luse.h"
#include <regex>
#include "pvector.h"
#include "modelPool.h"
#include "mapRoot.h"
#include "physTriangleMeshData.h"
#include "physConvexMeshData.h"
#include "physTriangleMesh.h"
#include "physConvexMesh.h"
#include "physShape.h"
#include "physRigidStaticNode.h"
#include "appBase.h"
#include "physMaterial.h"
#include "tfGlobals.h"
#include "texture.h"
#include "samplerState.h"
#include "nodePathCollection.h"
#include "textureCollection.h"

#ifdef TF_CLIENT
#include "tfClientBase.h"
#include "staticPartitionedObjectNode.h"
#include "mapLightingEffect.h"
#include "sceneGraphReducer.h"
#include "skyBoxMaterial.h"
#include "materialAttrib.h"
#include "material.h"
#include "mapRender.h"
#endif

/**
 *
 */
CLP(GameLevel)::
CLP(GameLevel)() :
  _lvl_data(nullptr)
{
}

#ifdef TF_CLIENT
/**
 * Does a flatten even stronger than flatten_strong().
 */
void CLP(GameLevel)::
flatten(NodePath &np) {
  SceneGraphReducer gr;
  gr.apply_attribs(np.node());
  gr.flatten(np.node(), ~0);
  gr.make_compatible_state(np.node());
  gr.collect_vertex_data(np.node(), 0);
  gr.unify(np.node(), false);
}
#endif

/**
 *
 */
void CLP(GameLevel)::
load_level_props() {
  const SpatialPartition *tree = _lvl_data->get_area_cluster_tree();

#ifdef TF_CLIENT
  PT(StaticPartitionedObjectNode) prop_node = new StaticPartitionedObjectNode("props");
  NodePath prop_root = _lvl.attach_new_node(prop_node);
  pvector<NodePath> light_nodes;
#else
  NodePath prop_root = _lvl.attach_new_node("props");
#endif

  Loader *loader = Loader::get_global_ptr();

  _prop_phys_root = NodePath("propPhysRoot");
  _prop_phys_root.hide();

  LoaderOptions lopts;

  // We keep track of the models that we loaded so we can evict
  // them from the ModelPool cache after we are done.
  // Prop models are typically only loaded once during level loads
  // so we can free up memory by not having them in the cache.
  pvector<PT(ModelRoot)> loaded_models;

  PT(PhysMaterial) temp_mat = new PhysMaterial(0.5f, 0.5f, 0.5f);

  for (int i = 0; i < _lvl_data->get_num_entities(); ++i) {
    MapEntity *ent = _lvl_data->get_entity(i);
    if (ent->get_class_name() != "prop_static") {
      continue;
    }

    PDXElement *props = ent->get_properties();

    if (!props->has_attribute("model")) {
      continue;
    }

    const PDXValue &model_val = props->get_attribute_value("model");
    if (!model_val.is_string()) {
      continue;
    }

    Filename model_filename = Filename::from_os_specific(
      std::regex_replace(model_val.get_string(), std::regex(".mdl"), ".bam"));
    NodePath prop_model = NodePath(loader->load_sync(model_filename, lopts));
    if (prop_model.is_empty()) {
      continue;
    }
    ModelRoot *prop_mdlroot = DCAST(ModelRoot, prop_model.node());
    loaded_models.push_back(prop_mdlroot);

#ifdef TF_CLIENT
    if (props->has_attribute("skin")) {
      int skin = props->get_attribute_value("skin").get_int();
      if (skin >= 0 && skin < prop_mdlroot->get_num_material_groups()) {
        prop_mdlroot->set_active_material_group(skin);
      }
    }
#endif

    LPoint3 pos;
    if (props->has_attribute("origin")) {
      props->get_attribute_value("origin").to_vec3(pos);
      prop_model.set_pos(pos);
    }

    if (props->has_attribute("angles")) {
      LVecBase3 phr;
      props->get_attribute_value("angles").to_vec3(phr);
      prop_model.set_hpr(phr[1] - 90, -phr[0], phr[2]);
    }

    // Set up collisions for the prop.
    PT(PhysRigidStaticNode) cnode;
    ModelRoot::CollisionInfo *cinfo = prop_mdlroot->get_collision_info();
    if (props->get_attribute_value("solid").get_int() != 0 &&
        cinfo != nullptr && cinfo->get_part(0)->mesh_data != nullptr) {
      const ModelRoot::CollisionPart *part = cinfo->get_part(0);
      PT(PhysShape) shape;
      if (part->concave) {
        PT(PhysTriangleMeshData) mdata = new PhysTriangleMeshData(part->mesh_data);
        if (mdata->generate_mesh()) {
          PhysTriangleMesh mesh(mdata);
          shape = new PhysShape(mesh, temp_mat);
        }
      } else {
        PT(PhysConvexMeshData) mdata = new PhysConvexMeshData(part->mesh_data);
        if (mdata->generate_mesh()) {
          PhysConvexMesh mesh(mdata);
          shape = new PhysShape(mesh, temp_mat);
        }
      }
      cnode = new PhysRigidStaticNode("propcoll");
      cnode->add_shape(shape);
      cnode->add_to_scene(base->get_phys_scene());
      NodePath cnp = _prop_phys_root.attach_new_node(cnode);
      cnp.set_transform(NodePath(), prop_model.get_net_transform());
    }

#ifdef TF_CLIENT
    // Perform lots of flattening to reduce nodes and geoms on props.
    prop_model.flatten_strong();
    NodePath lod_node = prop_model.find("**/+LODNode");
    if (!lod_node.is_empty()) {
      // Grab the first LOD and throw away the rest so we can flatten.
      prop_model = lod_node.get_child(0);
    }
    prop_model.flatten_strong();

    if (prop_model.get_num_children() == 1) {
      // If there's just one GeomNode under the ModelRoot, we can throw away
      // the ModelRoot.
      prop_model = prop_model.get_child(0);
    }

    prop_model.reparent_to(prop_root);

    bool in_3d_sky = false;
    // If the prop is positioned in the 3-D skybox, it needs to be parented
    // into the 3-D skybox scene graph.
    int leaf = tree->get_leaf_value_from_point(pos);
    if (leaf >= 0) {
      const AreaClusterPVS *pvs = _lvl_data->get_cluster_pvs(leaf);
      if (pvs->is_3d_sky_cluster()) {
        //prop_model.reparent_to(cbase->get_sky_3d_root());
        in_3d_sky = true;
      }
    }

    prop_model.set_effect(MapLightingEffect::make(CamBits::main));
    light_nodes.push_back(prop_model);

    prop_model.node()->set_final(true);
    if (!in_3d_sky) {
      prop_model.show_through(CamBits::shadow);
    }

#endif // TF_CLIENT
  }

#ifdef TF_CLIENT
  flatten(prop_root);

  for (NodePath &prop_model : light_nodes) {
    // Also, we can flatten better by pre-computing the lighting state once.
    const MapLightingEffect *light_effect = DCAST(MapLightingEffect,
      prop_model.get_effect(MapLightingEffect::get_class_type()));
    light_effect->compute_lighting(
      prop_model.get_net_transform(), _lvl_data,
      prop_model.get_bounds()->as_geometric_bounding_volume(),
      prop_model.get_parent().get_net_transform());
    CPT(RenderState) state = prop_model.get_state();
    state = state->compose(light_effect->get_current_lighting_state());
    prop_model.set_state(state);
    prop_model.clear_effect(MapLightingEffect::get_class_type());
    prop_model.flatten_light();
  }

  // Now partition the prop GeomNodes into the visibility tree.
  for (int i = 0; i < prop_root.get_num_children(); ++i) {
    GeomNode *child = DCAST(GeomNode, prop_root.get_child(i).node());
    prop_node->add_object(child);
  }
  prop_node->remove_all_children();
  prop_node->partition_objects(_lvl_data->get_num_clusters(), tree);

#endif // TF_CLIENT

  // Evict the loaded prop models from the ModelPool cache.
  for (ModelRoot *mdl : loaded_models) {
    ModelPool::release_model(mdl);
  }
}

/**
 *
 */
void CLP(GameLevel)::
load_level(const Filename &lvl_name) {
  unload_level();

  _lvl_name = lvl_name;

  Loader *loader = Loader::get_global_ptr();
  // Don't RAM or disk cache the level BAM file.
  LoaderOptions lopts(LoaderOptions::LF_search | LoaderOptions::LF_report_errors |
                      LoaderOptions::LF_no_cache);
  _lvl = NodePath(loader->load_sync(lvl_name, lopts));
  _lvl.reparent_to(base->get_render());
  NodePath lvl_root = _lvl.find("**/+MapRoot");
  lvl_root.set_light_off(-1);
  MapData *data = DCAST(MapRoot, lvl_root.node())->get_data();
  _lvl_data = data;

  // Make ure all the RAM copies of lightmaps and cube maps get thrown
  // away when they get uploaded to the graphics card.  They take up
  // a lot of memory.
  TextureCollection tc = _lvl.find_all_textures();
  for (int i = 0; i < tc.get_num_textures(); ++i) {
    Texture *tex = tc.get_texture(i);
    tex->set_keep_ram_image(false);
  }
  for (int i = 0; i < data->get_num_cube_maps(); ++i) {
    const MapCubeMap *mcm = data->get_cube_map(i);
    Texture *tex = mcm->get_texture();
    if (tex != nullptr) {
      tex->set_keep_ram_image(false);
      tex->set_minfilter(SamplerState::FT_linear);
      tex->set_magfilter(SamplerState::FT_linear);
      tex->clear_ram_mipmap_images();
    }
  }

  PT(PandaNode) dummy_root = new PandaNode("mapRoot");
  dummy_root->replace_node(lvl_root.node());

#ifdef TF_CLIENT
  NodePathCollection npc = _lvl.find_all_matches("**/+GeomNode");
  for (int i = 0; i < npc.get_num_paths(); ++i) {
    NodePath gnp = npc.get_path(i);
    GeomNode *gn = DCAST(GeomNode, gnp.node());
    // Delete skybox faces so we can do the actual source engine
    // skybox rendering.
    for (int j = gn->get_num_geoms() - 1; j >= 0; --j) {
      const Geom *geom = gn->get_geom(j);
      const RenderState *state = gn->get_geom_state(j);
      const MaterialAttrib *mattr;
      if (state->get_attrib(mattr)) {
        Material *mat = mattr->get_material();
        if (mat != nullptr && mat->is_of_type(SkyBoxMaterial::get_class_type())) {
          gn->remove_geom(j);
        }
      }
    }
  }

  _lvl.clear_model_nodes();
  flatten(_lvl);

  PT(MapRender) scene_top = new MapRender("top");
  scene_top->replace_node(base->get_render().node());
  scene_top->set_map_data(_lvl_data);

#endif

  load_level_props();

  _prop_phys_root.reparent_to(_lvl);

  _lvl.ls();
}

/**
 *
 */
void CLP(GameLevel)::
unload_level() {
  if (!_prop_phys_root.is_empty()) {
    // Remove all physics nodes from world geometry and static props.
    NodePathCollection npc = _prop_phys_root.find_all_matches("**/+PhysRigidActorNode");
    for (int i = 0; i < npc.get_num_paths(); ++i) {
      PhysRigidActorNode *actor = DCAST(PhysRigidActorNode, npc.get_path(i).node());
      actor->remove_from_scene(base->get_phys_scene());
    }
    _prop_phys_root.remove_node();
  }
  if (!_lvl.is_empty()) {
    _lvl.remove_node();
  }
  _lvl_data = nullptr;
  _lvl_name = "";
}

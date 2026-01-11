#include "gameManager.h"
#include "lvecBase2.h"
#include "mapData.h"
#include "networkClass.h"
#include "networkObject.h"
#include "notifyCategoryProxy.h"
#include "loader.h"
#include "mapRoot.h"
#include "spatialPartition.h"
#include "gameGlobals.h"
#include "staticPartitionedObjectNode.h"
#include "modelRoot.h"
#include "geomVertexFormat.h"
#include "shaderAttrib.h"
#include "modelPool.h"
#include "physRigidActorNode.h"
#include "gamePhysics.h"
#include "physRigidStaticNode.h"

#ifdef SERVER
#include "server/server.h"
#include "tfPlayer.h"
#include "randomizer.h"
#endif
#ifdef CLIENT
#include "client/client.h"
#include "mapLightingEffect.h"
#include "boundingBox.h"
#include "sceneGraphReducer.h"
#include "client/indexBufferCombiner.h"
#endif

NotifyCategoryDeclNoExport(gamemanager);
NotifyCategoryDef(gamemanager, "tf");

NetworkClass *GameManager::_network_class = nullptr;

struct JoinGameArgs {
  std::string player_name;

  static NetworkClass *get_network_class() {
    return _network_class;
  }
  static void init_network_class() {
    BEGIN_NETWORK_CLASS_NOBASE(JoinGameArgs);
    MAKE_NET_FIELD(JoinGameArgs, player_name, NetworkField::DT_string);
    END_NETWORK_CLASS();
  }
private:
  static NetworkClass *_network_class;
};
NetworkClass *JoinGameArgs::_network_class = nullptr;

struct JoinGameRespArgs {
  int tick_count;

  static NetworkClass *get_network_class() {
    return _network_class;
  }
  static void init_network_class() {
    BEGIN_NETWORK_CLASS_NOBASE(JoinGameRespArgs);
    MAKE_NET_FIELD(JoinGameRespArgs, tick_count, NetworkField::DT_uint32);
    END_NETWORK_CLASS();
  }
private:
  static NetworkClass *_network_class;
};
NetworkClass *JoinGameRespArgs::_network_class = nullptr;

/**
 *
 */
void GameManager::
s_recv_join_game(void *obj, void *pargs) {
#ifdef SERVER
  GameServer *server = GameServer::ptr();
  ClientConnection *client = server->get_client_sender();
  GameManager *mgr = (GameManager *)obj;
  JoinGameArgs *args = (JoinGameArgs *)pargs;
  gamemanager_cat.info()
    << "Got join game from client " << client->id << ", player name is " << args->player_name << "\n";

  // Make their player entity and mark them as the owner.
  // This will implicitly give the client interest into the
  // game zone, which we've assigned the player entity to.
  PT(TFPlayer) player = new TFPlayer;
  player->set_player_name(args->player_name);
  // Make the server aware of the player for this client.
  client->player = player;
  server->generate_object(player, game_zone, client);


  JoinGameRespArgs resp_args;
  resp_args.tick_count = server->get_tick_count();
  server->send_obj_message(mgr, "join_game_resp", &resp_args, client);
#endif
}

/**
 *
 */
void GameManager::
s_recv_join_game_resp(void *obj, void *pargs) {
#ifdef CLIENT
  GameManager *mgr = (GameManager *)obj;
  JoinGameRespArgs *args = (JoinGameRespArgs *)pargs;
  GameClient::ptr()->reset_simulation(args->tick_count);
  gamemanager_cat.info()
    << "Got join game response, reset simulation to tick " << args->tick_count << "\n";
#endif
}

/**
 *
 */
void GameManager::
generate() {
  NetworkObject::generate();
  globals.game = this;
#ifdef CLIENT
  gamemanager_cat.info()
    << "Game manager generated! Zone ID " << get_zone_id() << ", do id " << get_do_id() << "\n";
  gamemanager_cat.info()
    << "Level name is: " << _level_name << "\n";

  // Load the level the game is currently running.
  change_level(_level_name);

  // Level is loaded, send join message to the game manager.
  JoinGameArgs args;
  args.player_name = "bribri25";
  GameClient::ptr()->send_obj_message(this, "join_game", &args);
#endif
}

/**
 *
 */
void GameManager::
disable() {
  unload_level();
  assert(globals.game == this);
  globals.game = nullptr;
}

/**
 *
 */
void GameManager::
change_level(const Filename &level_filename) {
  unload_level();

  _level_name = level_filename.get_fullpath();

  // Don't RAM or disk cache the level BAM file.
  LoaderOptions opts(LoaderOptions::LF_search | LoaderOptions::LF_report_errors | LoaderOptions::LF_no_cache);
  Loader *loader = Loader::get_global_ptr();
  PT(PandaNode) level_top = loader->load_sync(level_filename, opts);
  assert(level_top != nullptr);
  NodePath level_path(level_top);

  NodePath lvl_root_path = level_path.find("**/+MapRoot");
  assert(!lvl_root_path.is_empty());
  lvl_root_path.set_light_off(-1);
  MapRoot *lvl_root = DCAST(MapRoot, lvl_root_path.node());
  MapData *data = lvl_root->get_data();

  // Make sure all the RAM copies of lightmaps and cube maps get thrown away
  // when they get uploaded to the graphics card.  They take up a lot of memory.
  TextureCollection textures = lvl_root_path.find_all_textures();
  for (int i = 0; i < textures.get_num_textures(); ++i) {
    Texture *tex = textures.get_texture(i);
    tex->set_keep_ram_image(false);
  }
  for (int i = 0; i < data->get_num_cube_maps(); ++i) {
    const MapCubeMap *cube = data->get_cube_map(i);
    Texture *cube_tex = cube->get_texture();
    if (cube_tex != nullptr) {
      cube_tex->set_keep_ram_image(false);
      // TODO: what is this for?  copied over from python DistributedGameBase.py
      cube_tex->set_minfilter(SamplerState::FT_linear);
      cube_tex->set_magfilter(SamplerState::FT_linear);
      cube_tex->clear_ram_mipmap_images();
    }
  }

  // I think this is to stop the MapRoot from doing BSP/PVS culling
  // on the world geometry faces.  It's faster for us to just
  // flatten it all together and draw it with no PVS culling.
  // Actually upon checking, MapRoot doesn't have any logic
  // for face culling, so I don't know.  Maybe it used to.
  PT(PandaNode) dummy_root = new PandaNode("map_root");
  dummy_root->replace_node(lvl_root);

  // Load props and overlays into scene.
  load_level_props();

  _prop_phys_root.reparent_to(_level_path);
}

/**
 *
 */
void GameManager::
unload_level() {
  if (!_prop_root.is_empty()) {
    _prop_root.remove_node();
  }
  if (!_prop_phys_root.is_empty()) {
    // Remove all prop collisions from physics scene.
    // Shouldn't this happen automatically though?
    NodePathCollection prop_physics_nodes = _prop_phys_root.find_all_matches("**/+PhysRigidActorNode");
    for (int i = 0; i < prop_physics_nodes.get_num_paths(); ++i) {
      PhysRigidActorNode *collision_node = DCAST(PhysRigidActorNode, prop_physics_nodes.get_path(i).node());
      collision_node->remove_from_scene(globals.physics_world);
    }
    _prop_phys_root.remove_node();
  }
  if (!_level_path.is_empty()) {
    _level_path.remove_node();
  }
  _level_data = nullptr;
  _level_name = "";
  _prop_models.clear();
}

/**
 *
 */
void GameManager::
load_level_props() {
  assert(_level_data != nullptr);
  assert(!_level_path.is_empty());

  Loader *loader = Loader::get_global_ptr();

  const SpatialPartition *tree = _level_data->get_area_cluster_tree();

  NodePath prop_root = globals.render.attach_new_node(new StaticPartitionedObjectNode("props"));
  _prop_root = prop_root;
  // Have props render into shadow maps.
  prop_root.show_through(CAMERAMASK_shadow);
  NodePath prop_phys_root("prop_phys_root");
  prop_phys_root.hide();

  // We keep track of the models that we loaded so we can evict them
  // from the ModelPoolc ache after we are done.
  // Prop models are typically only loaded one during level loads
  // and fully manipulated after, we so can free up memory by not
  // having them in the cache.
  pvector<PT(ModelRoot)> loaded_models;

  struct PropLightInfo {
    NodePath prop_model;
    bool has_vtx_light;
    bool in_3d_sky;
  };
  pvector<PropLightInfo> light_infos;

  GamePhysics *physics = GamePhysics::ptr();

  for (int i = 0; i < _level_data->get_num_static_props(); ++i) {
    const MapStaticProp *sprop = _level_data->get_static_prop(i);

    if (sprop->get_model_filename().get_basename_wo_extension().empty()) {
      continue;
    }

    Filename model_filename = sprop->get_model_filename();
    PT(PandaNode) prop_root_node = loader->load_sync(model_filename);
    if (prop_root_node == nullptr) {
      // Couldn't load the prop model.  Not found on disk?
      continue;
    }
    NodePath prop_model(prop_root_node);

    if (!prop_root_node->is_of_type(ModelRoot::get_class_type())) {
      continue;
    }
    ModelRoot *prop_model_root = DCAST(ModelRoot, prop_root_node);

    loaded_models.push_back(prop_model_root);

    // Apply the skin/material group to the prop model.
    if (sprop->get_skin() < prop_model_root->get_num_material_groups()) {
      prop_model_root->set_active_material_group(sprop->get_skin());
    }

    // Apply transform.
    prop_model.set_pos(sprop->get_pos());
    prop_model.set_hpr(sprop->get_hpr());

    LPoint3f pos = sprop->get_pos();

    // Setup collisions for the prop.
    PT(PhysRigidStaticNode) cnode;
    if (sprop->get_solid()) {
      PT(PhysShape) shape = physics->make_shape_from_model(prop_model_root);
      if (shape != nullptr) {
	cnode = new PhysRigidStaticNode("prop_collision");
	cnode->add_shape(shape);
	// Assign prop collision to world collision group.
	cnode->set_from_collide_mask(CollideMask_world);
	cnode->add_to_scene(physics->get_phys_world());
	// Match transform of physics actor to prop model.
	NodePath cnp = prop_phys_root.attach_new_node(cnode);
	cnp.set_transform(NodePath(), prop_model.get_net_transform());
      }
    }

    prop_model.flatten_light();
    NodePath lod_node = prop_model.find("**/+LODNode");
    if (!lod_node.is_empty()) {
      // Grab the first LOD and throw away the rest so we can flatten.
      prop_model = lod_node.get_child(0);
    }

    // Tack on baked per-vertex lighting.
    _geom_index = 0;
    bool has_any_vtx_light = r_process_prop_node(prop_root_node, sprop);

    prop_model.flatten_strong();

    if (prop_model.get_num_children() == 1) {
      // If there's just one GeomNode under the ModelRoot, we can throw away
      // the ModelRoot.
      prop_model = prop_model.get_child(0);
    }

    int prop_index = _prop_models.get_num_paths();
    _prop_models.add_path(prop_model);
    // TODO: prop index collision tag

    prop_model.reparent_to(prop_root);

    bool in_3d_sky = false;
    // TODO: 3d sky stuff
#ifdef CLIENT
    // If the prop is positioned in the 3-D skybox, it needs to be
    // parented into the 3-D skybox scene graph.
    // TODO...
    light_infos.push_back({ prop_model, has_any_vtx_light, in_3d_sky });
#endif

    prop_model.node()->set_final(true);
    if (!in_3d_sky) {
      prop_model.show_through(CAMERAMASK_shadow);
    }

    // TODO: sync transform on collision node
  }

#ifdef CLIENT
  for (PropLightInfo &linfo : light_infos) {
    // Also, we can flatten better by pre-computing the lighting state once.
    unsigned int flags = 0;
    if (linfo.in_3d_sky) {
      if (linfo.has_vtx_light) {
	flags = MapLightingEffect::F_default_baked_3d_sky;
      } else {
	flags = MapLightingEffect::F_default_dynamic | MapLightingEffect::F_no_sun;
	flags &= ~MapLightingEffect::F_dynamic_lights;
      }
    } else {
      if (linfo.has_vtx_light) {
	flags = MapLightingEffect::F_default_baked;
      } else {
	flags = MapLightingEffect::F_default_dynamic;
      }
    }

    // Create an effect for the purpose of computing the lighting state right now.
    // Compute the lighting once, then store the lighting state persistently on
    // the prop.
    CPT(MapLightingEffect) light_effect = DCAST(MapLightingEffect, MapLightingEffect::make(CAMERAMASK_main, false, flags));
    light_effect->compute_lighting(linfo.prop_model.get_net_transform(), _level_data,
				   DCAST(GeometricBoundingVolume, linfo.prop_model.get_bounds()),
				   linfo.prop_model.get_parent().get_net_transform());
    CPT(RenderState) state = linfo.prop_model.get_state();
    state = state->compose(light_effect->get_current_lighting_state());
    linfo.prop_model.set_state(state);
    linfo.prop_model.flatten_light();
  }

  // Add overlays/level decals into the static prop partitioning.
  for (int i = 0; i < _level_data->get_num_overlays(); ++i) {
    PandaNode *overlay = _level_data->get_overlay(i);
    if (!overlay->is_geom_node()) {
      // I'm not sure what this is for.  Can an overlay
      // not be a GeomNode at the root?  But have
      // specifically one node above it?
      if (overlay->get_num_children() == 0) {
	continue;
      }
      overlay = overlay->get_child(0);
      assert(overlay->is_geom_node());
    }

    NodePath overlay_path = NodePath(overlay).copy_to(prop_root);
    overlay_path.set_depth_write(false);
    overlay_path.set_bin("decal", 0);
    overlay_path.flatten_light();
    // Add a slight fudge to the bounding volume so axial decals don't have flat
    // bounding boxes.
    LPoint3f mins, maxs;
    overlay_path.calc_tight_bounds(mins, maxs);
    mins -= 1.0f;
    maxs += 1.0f;
    overlay_path.node()->set_bounds(new BoundingBox(mins, maxs));
  }

  // Attempt to share vertex buffers and combine GeomPrimitives
  // across the prop GeomNodes, without actually combining the
  // GeomNodes themselves, so we can still cull them effectively.
  SceneGraphReducer prop_gr;
  prop_gr.apply_attribs(prop_root.node());
  prop_gr.make_compatible_state(prop_root.node());
  prop_gr.collect_vertex_data(prop_root.node(), 0);
  prop_gr.unify(prop_root.node(), false);
  prop_gr.remove_unused_vertices(prop_root.node());

  // Now merge all the prop index buffers into as
  // few large index buffers as possible.
  IndexBufferCombiner ibc(prop_root);
  ibc.combine();

  // Throw all the prop geom nodes into the partition.
  NodePathCollection geom_nodes = prop_root.find_all_matches("**/+GeomNode");
  StaticPartitionedObjectNode *prop_partition = DCAST(StaticPartitionedObjectNode, prop_root.node());
  for (int i = 0; i < geom_nodes.get_num_paths(); ++i) {
    prop_partition->add_object(DCAST(GeomNode, geom_nodes.get_path(i).node()));
  }
  // Remove the actual prop geom nodes from the scene graph as
  // the partition is handling the rendering manually.
  prop_root.node()->remove_all_children();

  prop_partition->partition_objects(_level_data->get_num_clusters(), _level_data->get_area_cluster_tree());

#endif

  _prop_phys_root = prop_phys_root;

  // Now evict the prop models we loaded from the ModelPool cache.
  for (ModelRoot *model : loaded_models) {
    ModelPool::release_model(model);
  }
}

/**
 * Returns true if any node at this level and below had baked per-vertex
 * lighting applied.
 */
bool GameManager::
r_process_prop_node(PandaNode *node, const MapStaticProp *sprop) {
  bool has_any = false;
  if (node->is_geom_node()) {
    has_any = process_prop_geom_node(DCAST(GeomNode, node), sprop);
  }

  for (int i = 0; i < node->get_num_children(); ++i) {
    if (r_process_prop_node(node->get_child(i), sprop)) {
      has_any = true;
    }
  }

  return has_any;
}

/**
 * Returns true if the geom node had baked per-vertex lighting applied.
 */
bool GameManager::
process_prop_geom_node(GeomNode *node, const MapStaticProp *sprop) {
  bool has_any = false;

  for (int i = 0; i < node->get_num_geoms(); ++i) {
    const GeomVertexArrayData *baked_lighting = sprop->get_vertex_lighting(_geom_index);
    const Geom *geom = node->get_geom(i);
    const GeomVertexData *vdata = geom->get_vertex_data();

    // If we have baked lighting for this geom and the vertex count matches.
    if (baked_lighting != nullptr && (baked_lighting->get_num_rows() == vdata->get_num_rows())) {
      CPT(RenderState) state = node->get_geom_state(i);

      int arr_index = vdata->get_num_arrays();
      const GeomVertexFormat *fmt = vdata->get_format();

      PT(GeomVertexFormat) new_fmt = new GeomVertexFormat(*fmt);
      new_fmt->add_array(get_baked_vertex_lighting_array_format());
      CPT(GeomVertexFormat) reg_new_fmt = GeomVertexFormat::register_format(new_fmt);

      PT(GeomVertexData) new_vdata = new GeomVertexData(*vdata);
      new_vdata->set_format(reg_new_fmt);
      // Put the baked lighting array into the new vertex data.
      new_vdata->set_array(arr_index, baked_lighting);

      // Now replace the geom with one that uses the new vdata.
      PT(Geom) ngeom = geom->make_copy();
      ngeom->set_vertex_data(new_vdata);
      node->set_geom(i, ngeom);

      // Set the state that notifies the shader system that
      // baked vertex lighting is present.
      node->set_geom_state(i, state->compose(get_baked_vertex_lighting_state()));

      has_any = true;
    }

    ++_geom_index;
  }

  return has_any;
}

/**
 * Returns the vertex data format for static prop baked vertex lighting.
 * This will be tacked onto the existing vertex data format of any prop
 * that has baked lighting in the level, as a separate stream/vertex buffer.
 */
const GeomVertexArrayFormat *GameManager::
get_baked_vertex_lighting_array_format() {
  if (_baked_lighting_array_format == nullptr) {
    PT(GeomVertexArrayFormat) fmt = new GeomVertexArrayFormat;
    fmt->add_column(InternalName::make("vertex_lighting"), 4, GeomEnums::NT_uint8, GeomEnums::C_other);
    _baked_lighting_array_format = GeomVertexArrayFormat::register_format(fmt);
  }
  return _baked_lighting_array_format;
}

/**
 * Returns the render state that specifies the geometry has baked vertex
 * lighting.
 */
const RenderState *GameManager::
get_baked_vertex_lighting_state() {
  if (_baked_vertex_lighting_state == nullptr) {
    CPT(ShaderAttrib) sattr = ShaderAttrib::make();
    // The presence of this shader input on the state is what informs
    // the shader system that there's baked lighting.  Kind of dumb,
    // but I don't want to create an entire RenderAttrib type for this.
    sattr = DCAST(ShaderAttrib, sattr->set_shader_input("bakedVertexLighting", 0.0f));
    _baked_vertex_lighting_state = RenderState::make(sattr);
  }
  return _baked_vertex_lighting_state;
}

/**
 *
 */
void GameManager::
init_network_class() {
  JoinGameArgs::init_network_class();
  JoinGameRespArgs::init_network_class();

  BEGIN_NETWORK_CLASS_NOBASE(GameManager);
  _network_class->set_factory_func(make_GameManager);
  MAKE_NET_FIELD(GameManager, _game_name, NetworkField::DT_string);
  MAKE_NET_FIELD(GameManager, _level_name, NetworkField::DT_string);
  MAKE_NET_RPC(join_game, JoinGameArgs::get_network_class(), NetworkRPC::F_clsend, s_recv_join_game);
  MAKE_NET_RPC(join_game_resp, JoinGameRespArgs::get_network_class(), NetworkRPC::F_none, s_recv_join_game_resp);
  END_NETWORK_CLASS();
}

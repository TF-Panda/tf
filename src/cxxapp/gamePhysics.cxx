#include "gamePhysics.h"
#include "keyValues.h"
#include "pdxElement.h"
#include "string_utils.h"
#include "physSystem.h"
#include "gameGlobals.h"
#include "physConvexMeshData.h"
#include "physTriangleMeshData.h"
#include "physTriangleMesh.h"
#include "physConvexMesh.h"
#include "physShape.h"

GamePhysics *GamePhysics::_global_ptr = nullptr;

/**
 *
 */
void GamePhysics::
initialize() {
  PhysSystem *phys_system = PhysSystem::ptr();
  if (!phys_system->initialize()) {
    std::cerr << "Failed to initialize PhysX!\n";
    return;
  }
  _phys_world = new PhysScene;
  _phys_world->set_gravity(LVector3f(0, 0, -800.0f));
  _phys_world->set_fixed_timestep(0.015f);
  globals.physics_world = _phys_world;
}

/**
 * Returns a new physics shape using the collision info
 * for the given model.
 */
PT(PhysShape) GamePhysics::
make_shape_from_model(ModelRoot *model) {
  ModelRoot::CollisionInfo *cinfo = model->get_collision_info();
  if (cinfo == nullptr) {
    return nullptr;
  }
  if (cinfo->get_num_parts() == 0) {
    return nullptr;
  }
  // Assume there's just one part and make a shape for that part.
  const ModelRoot::CollisionPart *cpart = cinfo->get_part(0);
  if (cpart->mesh_data.empty()) {
    // No mesh data for the collision part.
    return nullptr;
  }

  // Annoying that these don't share a common base class.
  // If the part is marked concave, the mesh data is for a
  // triangle mesh, otherwise it's for a convex mesh.
  PT(PhysTriangleMeshData) tri_mdata;
  PT(PhysConvexMeshData) convex_mdata;
  bool mesh_generated;
  if (cpart->concave) {
    tri_mdata = new PhysTriangleMeshData(cpart->mesh_data);
    mesh_generated = tri_mdata->generate_mesh();
  } else {
    convex_mdata = new PhysConvexMeshData(cpart->mesh_data);
    mesh_generated = convex_mdata->generate_mesh();
  }

  if (!mesh_generated) {
    return nullptr;
  }

  std::string surface_prop = "default";

  // See if the model defines a surface prop for its collision shape.
  PDXElement *cdata = model->get_custom_data();
  if (cdata != nullptr) {
    if (cdata->has_attribute("surfaceprop")) {
      surface_prop = downcase(cdata->get_attribute_value("surfaceprop").get_string());
    }
  }
  // Grab the phys material for the surface prop.
  PhysMaterial *mat = get_surface_material(surface_prop);

  PT(PhysShape) shape;
  if (cpart->concave) {
    PhysTriangleMesh mesh(tri_mdata);
    shape = new PhysShape(mesh, mat);
  } else {
    PhysConvexMesh mesh(convex_mdata);
    shape = new PhysShape(mesh, mat);
  }

  return shape;
}

/**
 *
 */
bool GamePhysics::
load_surface_definitions() {
  Filename manifest_filename = "scripts/surfaceproperties_manifest.txt";
  PT(KeyValues) man_kv = KeyValues::load(manifest_filename);
  if (man_kv == nullptr) {
    std::cerr << "ERROR: Couldn't load surfaceproperties_manifest.txt\n";
    return false;
  }

  KeyValues *man_block = man_kv->get_child(0);
  for (size_t i = 0; i < man_block->get_num_keys(); ++i) {
    if (man_block->get_key(i) == "file") {
      Filename sp_filename = Filename::from_os_specific(man_block->get_value(i));
      if (!load_surface_definition_file(sp_filename)) {
	std::cout << "ERROR: Couldn't load " << sp_filename << " from manifest file\n";
	return false;
      }
    }
  }

  return true;
}

/**
 *
 */
bool GamePhysics::
load_surface_definition_file(const Filename &filename) {
  std::cerr << "Loading surface properties file " << filename << "\n";

  PT(KeyValues) kv = KeyValues::load(filename);
  if (kv == nullptr) {
    return false;
  }

  for (size_t i = 0; i < kv->get_num_children(); ++i) {
    KeyValues *surface_block = kv->get_child(i);
    std::string surface_name = downcase(surface_block->get_name());

    PT(SurfaceDefinition) def;
    if (surface_block->has_key("base")) {
      def = get_surface_def(downcase(surface_block->get_value("base")));
      if (def == nullptr) {
	std::cerr << "Base " << surface_block->get_value("base")
		  << " not found (referenced by surface " << surface_name << ")\n";
	return false;
      }
      def = new SurfaceDefinition(*def);
    } else {
      // If no base, use "default" as base.
      def = get_surface_def("default");
      if (def != nullptr) {
	def = new SurfaceDefinition(*def);
      } else {
	// This must be the surface definition for "default".
	def = new SurfaceDefinition;
      }
    }

    def->name = surface_name;

    for (size_t j = 0; j < surface_block->get_num_keys(); ++j) {
      std::string key = downcase(surface_block->get_key(j));
      const std::string &value = surface_block->get_value(j);

      // Yikes.
      if (key == "thickness") {
	string_to_float(key, def->thickness);
      } else if (key == "density") {
	string_to_float(key, def->density);
      } else if (key == "friction") {
	string_to_float(key, def->friction);
      } else if (key == "dampening") {
	string_to_float(key, def->dampening);
      } else if (key == "audioreflectivity") {
	string_to_float(key, def->audio_reflectivity);
      } else if (key == "audiohardnessfactor") {
	string_to_float(key, def->audio_hardness_factor);
      } else if (key == "audioroughnessfactor") {
	string_to_float(key, def->audio_roughness_factor);
      } else if (key == "scraperoughthreshold") {
	string_to_float(key, def->scrape_rough_threshold);
      } else if (key == "impacthardthreshold") {
	string_to_float(key, def->impact_hard_threshold);
      } else if (key == "jumpfactor") {
	string_to_float(key, def->jump_factor);
      } else if (key == "maxspeedfactor") {
	string_to_float(key, def->max_speed_factor);
      } else if (key == "climbable") {
	float climbable_val;
	string_to_float(key, climbable_val);
	def->climbable = climbable_val > 0;
      } else if (key == "stepleft") {
	def->step_left = value;
      } else if (key == "stepright") {
	def->step_right = value;
      } else if (key == "bulletimpact") {
	def->bullet_impact = value;
      } else if (key == "scraperough") {
	def->scrape_rough = value;
      } else if (key == "scrapesmooth") {
	def->scrape_smooth = value;
      } else if (key == "impacthard") {
	def->impact_hard = value;
      } else if (key == "impactsoft") {
	def->impact_soft = value;
      } else if (key == "gamematerial") {
	def->game_material = value;
      } else if (key == "break") {
	def->break_snd = value;
      } else if (key == "strain") {
	def->strain = value;
      } else if (key == "impactdecal") {
	def->impact_decal = value;
      }
    }

    _surface_defs[surface_name] = def;
  }

  return true;
}

#ifndef GAMEPHYSICS_H
#define GAMEPHYSICS_H

#include "physScene.h"
#include "pandabase.h"
#include "referenceCount.h"
#include "physShape.h"
#include "modelRoot.h"
#include "nodePath.h"

/**
 *
 */
class GamePhysics {
public:
  struct SurfaceDefinition : public ReferenceCount {
  public:
    std::string name;

    float thickness = 0.0f;
    float density = 0.0f;
    float friction = 0.0f;
    float dampening = 0.0f;
    float elasticity = 0.0f;

    float audio_reflectivity = 0.0f;
    float audio_hardness_factor = 0.0f;
    float audio_roughness_factor = 0.0f;

    float scrape_rough_threshold = 0.0f;
    float impact_hard_threshold = 0.0f;

    float jump_factor = 0.0f;
    float max_speed_factor = 0.0f;
    bool climbable = false;

    std::string game_material;

    // Sounds.
    std::string step_left, step_right;
    std::string bullet_impact, scrape_rough, scrape_smooth;
    std::string impact_hard, impact_soft, break_snd, strain;

    std::string impact_decal;

  public:
    PhysMaterial *get_phys_material();

  private:
    // Associated physics material.
    PT(PhysMaterial) _phys_material;
  };

public:
  void initialize();
  bool load_surface_definitions();
  bool load_surface_definition_file(const Filename &filename);

  PT(PhysShape) make_shape_from_model(ModelRoot *model);

  inline PhysMaterial *get_surface_material(const std::string &name);
  inline SurfaceDefinition *get_surface_def(const std::string &name) const;
  inline SurfaceDefinition *get_surface_def(PhysMaterial *mat) const;

  inline PhysScene *get_phys_world() const;

  inline static GamePhysics *ptr();

private:
  PT(PhysScene) _phys_world;

  typedef pflat_hash_map<std::string, PT(SurfaceDefinition), string_hash> SurfaceDefs;
  SurfaceDefs _surface_defs;

  typedef pflat_hash_map<PhysMaterial *, SurfaceDefinition *, pointer_hash> SurfacesByPhysMat;
  SurfacesByPhysMat _surfaces_by_phys_mat;

  static GamePhysics *_global_ptr;
};

/**
 *
 */
inline PhysScene *GamePhysics::
get_phys_world() const {
  return _phys_world;
}

/**
 * Returns the physics material for the named surface definition.
 */
inline PhysMaterial *GamePhysics::
get_surface_material(const std::string &name) {
  SurfaceDefinition *surf = get_surface_def(name);
  if (surf != nullptr) {
    return surf->get_phys_material();
  } else {
    return nullptr;
  }
}

/**
 * Returns the named surface definition.
 */
inline GamePhysics::SurfaceDefinition *GamePhysics::
get_surface_def(const std::string &name) const {
  SurfaceDefs::const_iterator it = _surface_defs.find(name);
  if (it != _surface_defs.end()) {
    return (*it).second;
  } else {
    return nullptr;
  }
}

/**
 * Returns the surface definition associated with the given physics
 * material.
 */
inline GamePhysics::SurfaceDefinition *GamePhysics::
get_surface_def(PhysMaterial *mat) const {
  SurfacesByPhysMat::const_iterator it = _surfaces_by_phys_mat.find(mat);
  if (it != _surfaces_by_phys_mat.end()) {
    return (*it).second;
  } else {
    return nullptr;
  }
}

/**
 *
 */
inline GamePhysics *GamePhysics::
ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new GamePhysics;
  }
  return _global_ptr;
}

#endif // GAMEPHYSICS_H

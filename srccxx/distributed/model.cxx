/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file model.cxx
 * @author brian
 * @date 2022-05-22
 */

#include "model.h"
#include "loader.h"
#include "pdxElement.h"
#include "pdxList.h"
#include "omniBoundingVolume.h"
#include "boundingBox.h"

/**
 * xyz
 */
Model::
Model() :
  _skin(0)
{
}

/**
 * Updates the model to use the currently selected material group/skin.
 */
void Model::
update_skin() {
  if (_model_node == nullptr) {
    return;
  }
  if (_skin >= 0 && _skin < (int)_model_node->get_num_material_groups()) {
    _model_node->set_active_material_group(_skin);
  }
}

/**
 * Sets the value of the bodygroup at the indicated index.  The node
 * collection at the index of the given value is shown while all other
 * collections in the bodygroup are hidden.
 */
void Model::
set_bodygroup_value(int bodygroup, int value) {
  nassertv(bodygroup >= 0 && bodygroup < (int)_bodygroups.size());
  Bodygroup &bg = _bodygroups[bodygroup];
  for (int i = 0; i < (int)bg._nodes.size(); ++i) {
    if (i == value) {
      bg._nodes[i].show();
    } else {
      bg._nodes[i].hide();
    }
  }
}

/**
 *
 */
void Model::
load_bodygroups() {
  if (_model_node == nullptr) {
    return;
  }

  PDXElement *data = _model_node->get_custom_data();
  if (data == nullptr) {
    return;
  }
  if (!data->has_attribute("bodygroups")) {
    return;
  }
  PDXList *bgs = data->get_attribute_value("bodygroups").get_list();
  for (size_t i = 0; i < bgs->size(); ++i) {
    PDXElement *bg_data = bgs->get(i).get_element();
    PDXList *nodes = bg_data->get_attribute_value("nodes").get_list();
    std::string name = bg_data->get_attribute_value("name").get_string();
    Bodygroup bg;
    bg._name = name;
    for (size_t j = 0; j < nodes->size(); ++j) {
      std::string pattern = nodes->get(j).get_string();
      if (pattern == "blank") {
        bg._nodes.push_back(NodePathCollection());
      } else {
        // Collect all nodes matching this pattern.
        bg._nodes.push_back(_model_np.find_all_matches("**/" + pattern));
      }
    }
  }

  // Default every bodygroup to the 0 index.
  for (size_t i = 0; i < _bodygroups.size(); ++i) {
    set_bodygroup_value((int)i, 0);
  }
}

/**
 *
 */
bool Model::
load_model(const Filename &filename) {
  unload_model();

  Loader *loader = Loader::get_global_ptr();
  _model_np = NodePath(loader->load_sync(filename));
  if (_model_np.is_empty()) {
    return false;
  }
  if (!_model_np.node()->is_of_type(ModelRoot::get_class_type())) {
    return false;
  }
  _model_node = DCAST(ModelRoot, _model_np.node());

  // Check for some custom model options.
  PDXElement *cdata = _model_node->get_custom_data();
  if (cdata != nullptr) {
    if (cdata->has_attribute("omni") && cdata->get_attribute_value("omni").get_bool()) {
      // Override the bounding volume with the "omni" bounding volume, making
      // the model always render even if outside the view frustum.
      _model_node->set_bounds(new OmniBoundingVolume);
    }
    if (cdata->has_attribute("bbox")) {
      // Model specifies a user bounding volume.
      // Note that this doesn't override the bounds of the geometry of
      // the model, it just unions with it.
      LPoint3 mins, maxs;
      PDXElement *bbox = cdata->get_attribute_value("bbox").get_element();
      bbox->get_attribute_value("mins").to_vec3(mins);
      bbox->get_attribute_value("maxs").to_vec3(maxs);
      _model_node->set_bounds(new BoundingBox(mins, maxs));
    }
  }

  // Cull the models's subgraph as a single unit.
  _model_node->set_final(true);

  // Collect all bodygroups and toggle the default ones.
  load_bodygroups();

  // Apply the currently selected skin.
  update_skin();

  return true;
}

/**
 * Removes the current model from the scene graph and all related data.
 */
void Model::
unload_model() {
  _bodygroups.clear();
  if (!_model_np.is_empty()) {
    _model_np.remove_node();
  }
  _model_node = nullptr;
}

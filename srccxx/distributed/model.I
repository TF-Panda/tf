/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file model.I
 * @author brian
 * @date 2022-05-22
 */

/**
 * Returns the NodePath of the model.
 */
INLINE NodePath Model::
get_model_np() const {
  return _model_np;
}

/**
 * Returns the ModelRoot node of the model.
 */
INLINE ModelRoot *Model::
get_model_node() const {
  return _model_node;
}

/**
 * Returns the custom data associated with the model.
 * Returns nullptr if no model is loaded or the model has no custom
 * data.
 */
INLINE PDXElement *Model::
get_model_custom_data() const {
  if (_model_node == nullptr) {
    return nullptr;
  }
  return _model_node->get_custom_data();
}

/**
 * Sets the active material group of the model.
 */
INLINE void Model::
set_skin(int skin) {
  _skin = skin;
  if (_model_node != nullptr && _model_node->get_active_material_group() != skin) {
    update_skin();
  }
}

/**
 * Returns the active material group of the model.
 */
INLINE int Model::
get_skin() const {
  return _skin;
}

/**
 * Returns the number of bodygroups in the model.
 */
INLINE int Model::
get_num_bodygroups() const {
  return (int)_bodygroups.size();
}

/**
 * Returns the index of the bodygroup with the indicated name, or -1 if no
 * bodygroup exists with that name.
 */
INLINE int Model::
find_bodygroup(const std::string &name) const {
  auto it = std::find_if(_bodygroups.begin(), _bodygroups.end(),
    [name](const Bodygroup &bg) {
      return bg._name == name;
    }
  );
  if (it == _bodygroups.end()) {
    return -1;
  } else {
    return it - _bodygroups.begin();
  }
}

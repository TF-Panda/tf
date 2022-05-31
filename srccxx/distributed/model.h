/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file model.h
 * @author brian
 * @date 2022-05-22
 */

#ifndef MODEL_H
#define MODEL_H

#include "tfbase.h"
#include "referenceCount.h"
#include "pointerTo.h"
#include "modelRoot.h"
#include "nodePath.h"
#include "nodePathCollection.h"
#include "pvector.h"

class PDXElement;

/**
 * Encapsulation of a model in the scene graph, implementing some
 * TF2 specific model features in a high-level interface.  This is the
 * base class for Actor.  Static models can just use the Model class,
 * but animated characters need to use the Actor class.
 */
class EXPCL_TF_DISTRIBUTED Model : public ReferenceCount {
public:
  /**
   * Bodygroups are collections of nodes that can be toggled on and off.
   */
  class Bodygroup {
  public:
    std::string _name;
    pvector<NodePathCollection> _nodes;
  };

  Model();
  virtual ~Model() = default;

  INLINE NodePath get_model_np() const;
  INLINE ModelRoot *get_model_node() const;
  INLINE PDXElement *get_model_custom_data() const;

  INLINE void set_skin(int skin);
  INLINE int get_skin() const;

  void update_skin();

  INLINE int get_num_bodygroups() const;
  INLINE int find_bodygroup(const std::string &name) const;
  void set_bodygroup_value(int bodygroup, int index);

  void load_bodygroups();

  virtual bool load_model(const Filename &filename);
  virtual void unload_model();

protected:
  // NodePath of the ModelRoot, the top level node in the loaded model.
  NodePath _model_np;
  PT(ModelRoot) _model_node;
  int _skin;
  typedef pvector<Bodygroup> Bodygroups;
  Bodygroups _bodygroups;
};

#include "model.I"

#endif // MODEL_H

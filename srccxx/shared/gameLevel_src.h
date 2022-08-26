/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file gameLevel_src.h
 * @author brian
 * @date 2022-05-19
 */

#include "tfshared.h"
#include "referenceCount.h"
#include "nodePath.h"
#include "mapData.h"
#include "filename.h"
#include "pointerTo.h"

/**
 * Handles loading game levels.
 */
class CLP(GameLevel) : public ReferenceCount {
public:
  CLP(GameLevel)();

#ifdef TF_CLIENT
  void flatten(NodePath &np);

  void r_process_prop_node(PandaNode *node, const MapStaticProp *sprop);
  void process_prop_geom_node(GeomNode *node, const MapStaticProp *sprop);
#endif

  void load_level_props();

  void unload_level();
  void load_level(const Filename &lvl_name);

public:
  NodePath _lvl;
  NodePath _prop_phys_root;
  PT(MapData) _lvl_data;
  Filename _lvl_name;

#ifdef TF_CLIENT
  int _geom_index;
#endif
};

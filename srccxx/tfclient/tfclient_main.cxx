/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfclient_main.cxx
 * @author brian
 * @date 2022-05-03
 */

#include "tfClientBase.h"
#include "graphicsEngine.h"
#include "memoryUsage.h"

#include "loader.h"
#include "config_anim.h"
#include "config_shader.h"
#include "tfclient_types.h"
#include "pointerTo.h"
#include "tfGlobals.h"
#include "mapLightingEffect.h"

#include "gameLevel.h"

/**
 *
 */
int
main(int argc, char *argv[]) {
  init_libanim();
  init_libshader();

  init_tfclient_types();

  TFClientBase tbase;
  base = &tbase;
  cbase = &tbase;
  tbase.initialize();

  Loader *loader = Loader::get_global_ptr();
  NodePath eng = NodePath(loader->load_sync("models/char/engineer"));
  eng.reparent_to(tbase.get_render());
  eng.set_y(75.0f);
  eng.set_h(180.0f);
  eng.set_z(-32.0f);
  eng.set_effect(MapLightingEffect::make(CamBits::main));

  tbase._camera.set_pos(0, -1024, 64);

  PT(GameLevel) lvl = new GameLevel;
  lvl->load_level("tr_target");

  tbase.run();
  return 0;
}

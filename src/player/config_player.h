/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_player.h
 * @author brian
 * @date 2022-05-23
 */

#ifndef CONFIG_PLAYER_H
#define CONFIG_PLAYER_H

#include "tfbase.h"
#include "dconfig.h"
#include "notifyCategoryProxy.h"

ConfigureDecl(config_player, EXPCL_TF_PLAYER, EXPTP_TF_PLAYER);

extern EXPCL_TF_PLAYER void init_libplayer();

#endif // CONFIG_PLAYER_H

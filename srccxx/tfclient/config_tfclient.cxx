/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_tfclient.cxx
 * @author brian
 * @date 2022-05-03
 */

#include "config_tfclient.h"

NotifyCategoryDef(tf, "");

ConfigVariableInt fov
("fov", 75,
 PRC_DESC("Specifies the field-of-view angle of the 3-D world and skybox "
          "camera lenses."));
ConfigVariableInt viewmodel_fov
("viewmodel-fov", 54,
 PRC_DESC("Specifies the field-of-view angle of the viewmodel camera lens."));

ConfigVariableDouble sfx_volume
("sfx-volume", 1.0,
 PRC_DESC("Specifies the master volume for all sound effects in the game."));
ConfigVariableDouble music_volume
("music-volume", 1.0,
 PRC_DESC("Specifies the master volume for all music in the game."));

ConfigVariableBool want_pstats
("want-pstats", false,
 PRC_DESC("If true, the game will attempt to connect to a PStats server "
          "as soon as the game is launched.  PStats is Panda's top-down "
          "performance analysis tool."));

ConfigVariableInt client_update_rate
("client-update-rate", 66,
 PRC_DESC("Specifies the number of updates per second the client should "
          "receive from the server.  This is clamped to the server's "
          "simulation rate."));
ConfigVariableInt client_cmd_rate
("client-cmd-rate", 66,
 PRC_DESC("Specifies the number of commands the client sends to the server "
          "per second.  This cannot be higher than the server's simulation "
          "rate."));

ConfigVariableString player_name
("player-name", "Player",
 PRC_DESC("Sets the name of the player."));

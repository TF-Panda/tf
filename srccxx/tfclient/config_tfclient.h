/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_tfclient.h
 * @author brian
 * @date 2022-05-03
 */

#ifndef CONFIG_TFCLIENT_H
#define CONFIG_TFCLIENT_H

#include "pandabase.h"
#include "configVariableInt.h"
#include "configVariableBool.h"
#include "configVariableDouble.h"
#include "notifyCategoryProxy.h"
#include "configVariableString.h"

NotifyCategoryDeclNoExport(tf);

extern ConfigVariableInt fov;
extern ConfigVariableInt viewmodel_fov;

extern ConfigVariableDouble sfx_volume;
extern ConfigVariableDouble music_volume;

extern ConfigVariableBool want_pstats;

extern ConfigVariableInt client_update_rate;
extern ConfigVariableInt client_cmd_rate;

extern ConfigVariableString player_name;

#endif // CONFIG_TFCLIENT_H

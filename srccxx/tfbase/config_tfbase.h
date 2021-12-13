/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_tfbase.h
 * @author brian
 * @date 2021-11-11
 */

#ifndef CONFIG_TFBASE_H
#define CONFIG_TFBASE_H

#include "tfbase.h"
#include "dconfig.h"
#include "notifyCategoryProxy.h"

ConfigureDecl(config_tfbase, EXPCL_TF_TFBASE, EXPTP_TF_TFBASE);
NotifyCategoryDecl(tfbase, EXPCL_TF_TFBASE, EXPTP_TF_TFBASE);

extern EXPCL_TF_TFBASE void init_libtfbase();

#endif // CONFIG_TFBASE_H

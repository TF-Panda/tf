/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file config_tfdistributed.h
 * @author brian
 * @date 2022-05-10
 */

#ifndef CONFIG_TFDISTRIBUTED_H
#define CONFIG_TFDISTRIBUTED_H

#include "tfbase.h"
#include "dconfig.h"
#include "notifyCategoryProxy.h"
#include <stdint.h>
#include "pset.h"

ConfigureDecl(config_tfdistributed, EXPCL_TF_DISTRIBUTED, EXPTP_TF_DISTRIBUTED);
NotifyCategoryDecl(tfdistributed, EXPCL_TF_DISTRIBUTED, EXPTP_TF_DISTRIBUTED);

typedef uint32_t doid_t;
typedef uint32_t zoneid_t;
typedef pflat_set<zoneid_t> zoneset_t;

extern EXPCL_TF_DISTRIBUTED void init_libtfdistributed();

#endif // CONFIG_TFDISTRIBUTED_H

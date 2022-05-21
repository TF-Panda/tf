/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file netMessages.h
 * @author brian
 * @date 2022-05-07
 */

#ifndef NETMESSAGES_H
#define NETMESSAGES_H

#include "pandabase.h"

enum NetMessage : uint8_t {
  NM_cl_hello,
  NM_sv_hello_resp,

  NM_sv_change_level,
  NM_cl_level_loaded,

  NM_cl_set_update_rate,
  NM_cl_set_cmd_rate,
  NM_cl_disconnect,

  NM_sv_tick,
  NM_cl_tick,

  NM_b_object_message,

  NM_sv_generate_object,
  NM_sv_disable_object,
  NM_sv_delete_object,
};

#endif // NETMESSAGES_H

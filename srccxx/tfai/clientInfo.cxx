/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientInfo.cxx
 * @author brian
 * @date 2022-05-06
 */

#include "clientInfo.h"
#include "clientFrame.h"

IMPLEMENT_CLASS(ClientInfo);

ClientInfo::
ClientInfo() :
  _id(0),
  _connection(INVALID_STEAM_NETWORK_CONNECTION_HANDLE),
  _state(CS_unverified),
  _update_rate(0),
  _update_interval(0),
  _next_update_time(0),
  _cmd_rate(0),
  _cmd_interval(0),
  _prev_tick_count(0),
  _tick_count(0),
  _delta_tick(-1)
{
}

/**
 *
 */
void ClientInfo::
setup_pack_info(FrameSnapshot *snapshot) {
  PT(ClientFrame) frame = new ClientFrame(snapshot);
  int len = _frame_mgr.add_client_frame(frame);
  while (len > max_client_frames) {
    _frame_mgr.remove_oldest_frame();
    --len;
  }
}

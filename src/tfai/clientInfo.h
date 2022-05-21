/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientInfo.h
 * @author brian
 * @date 2022-05-06
 */

#ifndef CLIENTINFO_H
#define CLIENTINFO_H

#include "pandabase.h"
#include "steamnet_includes.h"
#include "netAddress.h"
#include "typedReferenceCount.h"
#include "pset.h"
#include "clientFrameManager.h"
#include "config_tfdistributed.h"

class FrameSnapshot;

/**
 * Tracks information about a single client connected to the server and
 * playing.
 */
class ClientInfo : public TypedReferenceCount {
  DECLARE_CLASS(ClientInfo, TypedReferenceCount);

public:
  ClientInfo();

  enum ClientState {
    CS_unverified,
    CS_loading_level,
    CS_playing,
  };

  void setup_pack_info(FrameSnapshot *snapshot);

  INLINE bool needs_update(PN_stdfloat time) const;

  uint32_t _id;
  SteamNetworkConnectionHandle _connection;
  NetAddress _net_address;

  ClientState _state;

  // How often the client should receive state updates from us.
  unsigned char _update_rate;
  PN_stdfloat _update_interval;
  PN_stdfloat _next_update_time;

  // How often the client should send us player commands.
  unsigned char _cmd_rate;
  PN_stdfloat _cmd_interval;

  uint32_t _prev_tick_count;
  uint32_t _tick_count;
  int _delta_tick;

  std::string _name;

  zoneset_t _interest;

  ClientFrameManager _frame_mgr;
};

#include "clientInfo.I"

#endif // CLIENTINFO_H

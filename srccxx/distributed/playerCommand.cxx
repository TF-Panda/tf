/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file playerCommand.cxx
 * @author brian
 * @date 2022-05-23
 */

#include "playerCommand.h"
#include "datagram.h"
#include "datagramIterator.h"
#include "randomizer.h"

/**
 *
 */
void PlayerCommand::
clear() {
  _buttons = 0;
  _view_angles.set(0.0f, 0.0f, 0.0f);
  _move.set(0.0f, 0.0f, 0.0f);
  _weapon_select = -1;
  _has_been_predicted = false;
  _tick_count = 0;
  _command_number = 0;
  _random_seed = 0;
}

/**
 *
 */
PlayerCommand PlayerCommand::
from_datagram(DatagramIterator &scan, const PlayerCommand &prev) {
  // Assume no change.
  PlayerCommand cmd = prev;

  if (scan.get_uint8()) {
    cmd._command_number = scan.get_uint32();
  } else {
    // Assume steady increment.
    cmd._command_number = prev._command_number + 1;
  }

  Randomizer random(cmd._command_number);
  cmd._random_seed = random.random_int(0xffffffff);

  if (scan.get_uint8()) {
    cmd._tick_count = scan.get_uint32();
  } else {
    // Assume steady increment.
    cmd._tick_count = prev._tick_count + 1;
  }

  if (scan.get_uint8()) {
    cmd._view_angles.read_datagram_fixed(scan);
  }

  if (scan.get_uint8()) {
    cmd._move.read_datagram_fixed(scan);
  }

  if (scan.get_uint8()) {
    cmd._buttons = scan.get_uint32();
  }

  if (scan.get_uint8()) {
    cmd._weapon_select = scan.get_int8();
  }

  return cmd;
}

/**
 *
 */
void PlayerCommand::
write_datagram(Datagram &dg, const PlayerCommand &prev) {
  if (_command_number != prev._command_number) {
    dg.add_uint8(1);
    dg.add_uint32(_command_number);
  } else {
    dg.add_uint8(0);
  }

  if (_tick_count != prev._tick_count) {
    dg.add_uint8(1);
    dg.add_uint32(_tick_count);
  } else {
    dg.add_uint8(0);
  }

  if (_view_angles != prev._view_angles) {
    dg.add_uint8(1);
    _view_angles.write_datagram_fixed(dg);
  } else {
    dg.add_uint8(0);
  }

  if (_move != prev._move) {
    dg.add_uint8(1);
    _move.write_datagram_fixed(dg);
  } else {
    dg.add_uint8(0);
  }

  if (_buttons != prev._buttons) {
    dg.add_uint8(1);
    dg.add_uint32(_buttons);
  } else {
    dg.add_uint8(0);
  }

  if (_weapon_select != prev._weapon_select) {
    dg.add_uint8(1);
    dg.add_int8(_weapon_select);
  } else {
    dg.add_uint8(0);
  }
}

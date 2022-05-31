/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file playerCommand.h
 * @author brian
 * @date 2022-05-23
 */

#ifndef PLAYERCOMMAND_H
#define PLAYERCOMMAND_H

#include "tfbase.h"
#include "luse.h"

class Datagram;
class DatagramIterator;

/**
 *
 */
class EXPCL_TF_DISTRIBUTED PlayerCommand {
public:
  INLINE PlayerCommand();

  void clear();

  static PlayerCommand from_datagram(DatagramIterator &scan, const PlayerCommand &prev);
  void write_datagram(Datagram &dg, const PlayerCommand &prev);

public:
  unsigned int _buttons;

  LVecBase3f _view_angles;

  LVecBase3f _move;

  int _weapon_select;

  unsigned int _tick_count;
  unsigned int _command_number;
  unsigned int _random_seed;

  bool _has_been_predicted;
};

#include "playerCommand.I"

#endif // PLAYERCOMMAND_H

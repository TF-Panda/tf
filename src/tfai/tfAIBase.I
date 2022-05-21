/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfAIBase.I
 * @author brian
 * @date 2022-05-09
 */

/**
 *
 */
INLINE ServerRepository *TFAIBase::
get_air() const {
  return DCAST(ServerRepository, _net);
}

/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedGameAI.I
 * @author brian
 * @date 2022-05-09
 */

/**
 * Returns the filename of the current level.
 */
INLINE const std::string &DistributedGameAI::
get_level_name() const {
  return _level_name;
}

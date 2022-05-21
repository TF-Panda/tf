/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedObjectAI.I
 * @author brian
 * @date 2022-05-18
 */

/**
 *
 */
INLINE void DistributedObjectAI::
set_owner(ClientInfo *client) {
  _owner = client;
}

/**
 *
 */
INLINE ClientInfo *DistributedObjectAI::
get_owner() const {
  return _owner;
}

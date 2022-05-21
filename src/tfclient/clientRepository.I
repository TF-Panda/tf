/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file clientRepository.I
 * @author brian
 * @date 2022-05-05
 */

/**
 *
 */
INLINE void ClientRepository::
reader_poll_until_empty() {
  if (!_connected) {
    return;
  }

  while (reader_poll_once()) {
  }
}

/**
 *
 */
INLINE bool ClientRepository::
is_connected() const {
  return _connected;
}

/**
 *
 */
INLINE const NetAddress &ClientRepository::
get_server_address() const {
  return _server_address;
}

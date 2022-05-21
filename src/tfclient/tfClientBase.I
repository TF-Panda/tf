/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfClientBase.I
 * @author brian
 * @date 2022-05-03
 */

/**
 * Returns the GraphicsWindow/Output object that the game renders into.
 * This corresponds directly to a window on screen.
 */
INLINE GraphicsOutput *TFClientBase::
get_output() const {
  return _graphics_output;
}

/**
 * Returns the GraphicsPipe that the game is using to render with.
 */
INLINE GraphicsPipe *TFClientBase::
get_pipe() const {
  return _graphics_pipe;
}

/**
 * Returns the ClientRepository managing network connection to the server
 * and all distributed objects.
 *
 * Returns NULL if the client is not in game.
 */
INLINE ClientRepository *TFClientBase::
get_cr() const {
  return DCAST(ClientRepository, _net);
}

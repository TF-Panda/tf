#include "gameGlobals.h"

GameGlobals globals;

#ifdef CLIENT
#include "tfPlayer.h"

/**
 *
 */
LocalTFPlayer *GameGlobals::
get_local_tf_player() const {
  LocalTFPlayer *local_player = nullptr;
  if (local_avatar != nullptr) {
    local_player = local_avatar->get_local_player();
  }
  return local_player;
}
#endif

#include "gameGlobals.h"

GameGlobals globals;

#ifdef SERVER
#include "server/server.h"
#endif

#ifdef CLIENT
#include "tfPlayer.h"
#include "client/client.h"

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

NetworkObject *GameGlobals::
get_do_by_id(DO_ID do_id) const {
#ifdef CLIENT
  return cr->get_do(do_id);
#else
  return sv->get_do_by_id(do_id);
#endif
}

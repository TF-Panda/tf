#include "networkClasses.h"
#include "vectorNetClasses.h"
#include "networkClassRegistry.h"
#include "gameManager.h"
#include "tfPlayer.h"

//#include "entity.h"

/**
 *
 */
void
init_network_classes() {
  init_vector_net_classes();

  // Put additional network classes here.

  //Entity::init_type();
  //Entity::init_network_class();

  GameManager::init_network_class();
  Entity::init_network_class();
  TFPlayer::init_network_class();

  TFPlayer::get_type_network_class()->output(std::cerr);

  NetworkClassRegistry *reg = NetworkClassRegistry::ptr();
  reg->build_ids();
}

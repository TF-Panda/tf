#include "networkClasses.h"
#include "vectorNetClasses.h"
#include "networkClassRegistry.h"
#include "gameManager.h"
#include "entity.h"
#include "tfPlayer.h"
#include "weapon.h"
#include "viewModel.h"

/**
 * Initializes all network classes.
 */
void
init_network_classes() {
  init_vector_net_classes();

  // Put additional network classes here.

  GameManager::init_network_class();
  Entity::init_network_class();
  TFPlayer::init_network_class();
  Weapon::init_network_class();
  ViewModel::init_network_class();

  NetworkClassRegistry *reg = NetworkClassRegistry::ptr();
  reg->build_ids();
}

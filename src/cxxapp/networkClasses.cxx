#include "networkClasses.h"
#include "vectorNetClasses.h"
#include "networkClassRegistry.h"

#include "entity.h"

/**
 *
 */
void
init_network_classes() {
  init_vector_net_classes();

  // Put additional network classes here.

  Entity::init_type();
  Entity::init_network_class();

  
  
  NetworkClassRegistry *reg = NetworkClassRegistry::ptr();
  reg->build_ids();
}

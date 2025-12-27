#include "networkClassRegistry.h"
#include "networkClass.h"

NetworkClassRegistry *NetworkClassRegistry::_ptr = nullptr;

/**
 * 
 */
void
NetworkClassRegistry::register_class(NetworkClass *cls) {
  // Inherit fields from parent onto child class if it has a parent.
  cls->inherit_fields();

  _classes.push_back(cls);
  _classes_by_name.insert({cls->get_name(), cls});
}

/**
 * 
 */
void
NetworkClassRegistry::build_ids() {
  // Order all classes by name.  Assign IDs in order.

  size_t current_id = 1u;
  std::sort(_classes.begin(), _classes.end(),
            [](NetworkClass *a, NetworkClass *b) {
              return a->get_name() < b->get_name();
            });

  pvector<NetworkField *> all_fields;
  pvector<NetworkField *> local_fields;

  for (size_t i = 0; i < _classes.size(); ++i) {
    local_fields.clear();

    _classes[i]->set_id(current_id++);
    _classes_by_id.insert({_classes[i]->get_id(), _classes[i]});

    for (size_t j = 0; j < _classes[i]->get_num_fields(); ++j) {
      local_fields.push_back(_classes[i]->get_field(j));
    }

    // Sort local fields within class (not including inherited ones), then add
    // to global field list.
    std::sort(
        local_fields.begin(), local_fields.end(),
        [](NetworkField *a, NetworkField *b) { return a->name < b->name; });

    all_fields.insert(all_fields.end(), local_fields.begin(),
                      local_fields.end());
  }

  current_id = 1u;
  // Now assign field IDs.
  for (size_t i = 0; i < all_fields.size(); ++i) {
    all_fields[i]->id = current_id++;
  }
}


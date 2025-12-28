#ifndef NETWORKCLASSREGISTRY_H
#define NETWORKCLASSREGISTRY_H

#include <cstddef>
#include "pandabase.h"
#include "pvector.h"
#include "pmap.h"
#include "pnotify.h"

class NetworkClass;

/**
 *
 */
class NetworkClassRegistry {
public:
  void register_class(NetworkClass *cls);
  void build_ids();

  inline NetworkClass *get_class_by_name(const std::string &name) const;
  inline NetworkClass *get_class_by_id(uint16_t id) const;

  inline size_t get_num_classes() const;
  inline NetworkClass *get_class(size_t n) const;

private:
  typedef pvector<NetworkClass *> Classes;
  typedef pflat_hash_map<uint16_t, NetworkClass *, integer_hash<uint16_t>> ClassesByID;
  typedef pflat_hash_map<std::string, NetworkClass *, string_hash> ClassesByName;
  Classes _classes;
  ClassesByID _classes_by_id;
  ClassesByName _classes_by_name;

public:
  inline static NetworkClassRegistry *ptr();

private:
  static NetworkClassRegistry *_ptr;
};

/**
 *
 */
inline NetworkClass *
NetworkClassRegistry::get_class_by_name(const std::string &name) const {
  ClassesByName::const_iterator it = _classes_by_name.find(name);
  if (it != _classes_by_name.end()) {
    return (*it).second;
  }
  return nullptr;
}

/**
 *
 */
inline NetworkClass *
NetworkClassRegistry::get_class_by_id(uint16_t id) const {
  ClassesByID::const_iterator it = _classes_by_id.find(id);
  if (it != _classes_by_id.end()) {
    return (*it).second;
  }
  return nullptr;
}

/**
 *
 */
inline size_t
NetworkClassRegistry::get_num_classes() const {
  return _classes.size();
}

/**
 *
 */
inline NetworkClass *
NetworkClassRegistry::get_class(size_t n) const {
  nassertr(n < _classes.size(), nullptr);
  return _classes[n];
}

/**
 *
 */
inline NetworkClassRegistry *NetworkClassRegistry::
ptr() {
  if (_ptr == nullptr) {
    _ptr = new NetworkClassRegistry;
  }
  return _ptr;
}

#endif // NETWORKCLASSREGISTRY_H

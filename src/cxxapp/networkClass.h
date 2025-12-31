#ifndef NETWORKCLASS_H
#define NETWORKCLASS_H

#include "datagram.h"
#include "datagramIterator.h"
#include "pvector.h"
#include "pmap.h"
#include "networkField.h"
#include "networkRPC.h"
#include "networkClassRegistry.h"

class NetworkObject;
struct NetworkRPC;

/**
 * Definition of a networked class and its serialized fields.
 */
class NetworkClass {
public:
  typedef NetworkObject *(*EntityFactoryFunc)();

public:
  inline NetworkClass(const std::string &name, EntityFactoryFunc func = nullptr, NetworkClass *parent = nullptr);

  inline void set_parent(NetworkClass *cls);
  inline NetworkClass *get_parent() const;

  inline void add_field(NetworkField *field);
  inline void add_rpc(NetworkRPC *rpc);

  inline void set_factory_func(EntityFactoryFunc func);
  inline EntityFactoryFunc get_factory_func() const;

  inline void set_id(size_t id);
  inline size_t get_id() const;

  inline const std::string &get_name() const;

  inline size_t get_num_fields() const;
  inline NetworkField *get_field(size_t n) const;

  inline size_t get_num_inherited_fields() const;
  inline NetworkField *get_inherited_field(size_t n) const;

  inline size_t get_num_rpcs() const;
  inline NetworkRPC *get_rpc(size_t n) const;

  inline size_t get_num_inherited_rpcs() const;
  inline NetworkRPC *get_inherited_rpc(size_t n) const;
  inline NetworkRPC *get_inherited_rpc_by_name(const std::string &name) const;
  inline int find_inherited_rpc(const std::string &name) const;

  inline void set_stride(size_t stride);
  inline size_t get_stride() const;

  void inherit_fields();

  void write(void *object, Datagram &dg) const;
  void read(void *object, DatagramIterator &scan) const;

  void output(std::ostream &out, int indent = 0) const;

  void construct_fields(void *object) const;
  void destruct_fields(void *object) const;

  template<typename Cls, typename Var>
  inline NetworkField *make_field(const std::string &name, Var Cls::*var);
  template<typename Cls, typename Var>
  inline NetworkField *make_field(const std::string &name, Var Cls::*var, NetworkField::DataType encoding, int divisor = 1, float modulo = 0.0f);
  template<typename Var>
  inline NetworkField *make_indirect_field(const std::string &name, NetworkField::IndirectFetchFunc fetch, NetworkField::IndirectWriteFunc write);
  template<typename Var>
  inline NetworkField *make_indirect_field(const std::string &name, NetworkField::IndirectFetchFunc fetch, NetworkField::IndirectWriteFunc write, NetworkField::DataType encoding, int divisor = 1, float modulo = 0.0f);
  template<typename Cls, typename Var>
  inline NetworkField *make_struct_field(const std::string &name, Var Cls::*var, NetworkClass *struct_class);
  template<typename Var>
  inline NetworkField *make_indirect_struct_field(const std::string &name, NetworkClass *struct_class, NetworkField::IndirectFetchFunc fetch, NetworkField::IndirectWriteFunc write);

private:
  std::string _name;
  EntityFactoryFunc _factory_func;
  size_t _id;
  NetworkClass *_parent;
  bool _built_inherited_fields;
  size_t _stride;

  typedef pvector<NetworkField *> Fields;
  typedef pflat_hash_map<uint16_t, NetworkField *, integer_hash<uint16_t>> FieldsByID;
  typedef pflat_hash_map<std::string, NetworkField *, string_hash> FieldsByName;

  typedef pvector<NetworkRPC *> RPCs;
  typedef pflat_hash_map<uint16_t, NetworkRPC *, integer_hash<uint16_t>> RPCsByID;
  typedef pflat_hash_map<std::string, NetworkRPC *, string_hash> RPCsByName;

  Fields _fields;
  Fields _inherited_fields;
  FieldsByID _fields_by_id;
  FieldsByName _fields_by_name;

  RPCs _rpcs;
  RPCs _inherited_rpcs;
  RPCsByID _rpcs_by_id;
  RPCsByName _rpcs_by_name;
};

/**
 *
 */
inline NetworkClass::
NetworkClass(const std::string &name, EntityFactoryFunc factory, NetworkClass *parent) :
  _name(name),
  _factory_func(factory),
  _id(0u),
  _built_inherited_fields(false),
  _parent(parent),
  _stride(0u)
{
}

/**
 *
 */
inline void NetworkClass::
set_parent(NetworkClass *parent) {
  _parent = parent;
}

/**
 *
 */
inline NetworkClass *NetworkClass::
get_parent() const {
  return _parent;
}

/**
 *
 */
inline void NetworkClass::
add_field(NetworkField *field) {
  _fields.push_back(field);
}

/**
 *
 */
inline void NetworkClass::
add_rpc(NetworkRPC *rpc) {
  _rpcs.push_back(rpc);
}

/**
 *
 */
inline void NetworkClass::
set_factory_func(NetworkClass::EntityFactoryFunc func) {
  _factory_func = func;
}

/**
 *
 */
inline NetworkClass::EntityFactoryFunc NetworkClass::
get_factory_func() const {
  return _factory_func;
}

/**
 *
 */
inline const std::string &NetworkClass::
get_name() const {
  return _name;
}

/**
 *
 */
inline void NetworkClass::
set_id(size_t id) {
  _id = id;
}

/**
 *
 */
inline size_t NetworkClass::
get_id() const {
  return _id;
}

/**
 *
 */
inline size_t NetworkClass::
get_num_fields() const {
  return _fields.size();
}

/**
 *
 */
inline NetworkField *NetworkClass::
get_field(size_t n) const {
  nassertr(n < _fields.size(), nullptr);
  return _fields[n];
}

/**
 *
 */
inline size_t NetworkClass::
get_num_inherited_fields() const {
  return _inherited_fields.size();
}

/**
 *
 */
inline NetworkField *NetworkClass::
get_inherited_field(size_t n) const {
  nassertr(n < _inherited_fields.size(), nullptr);
  return _inherited_fields[n];
}

/**
 *
 */
inline size_t NetworkClass::
get_num_rpcs() const {
  return _rpcs.size();
}

/**
 *
 */
inline NetworkRPC *NetworkClass::
get_rpc(size_t n) const {
  nassertr(n < _rpcs.size(), nullptr);
  return _rpcs[n];
}

/**
 *
 */
inline size_t NetworkClass::
get_num_inherited_rpcs() const {
  return _inherited_rpcs.size();
}

/**
 *
 */
inline NetworkRPC *NetworkClass::
get_inherited_rpc(size_t n) const {
  nassertr(n < _inherited_rpcs.size(), nullptr);
  return _inherited_rpcs[n];
}

/**
 * Returns the RPC on the network class with the given name, or nullptr if no
 * such RPC exists.
 */
inline NetworkRPC *NetworkClass::
get_inherited_rpc_by_name(const std::string &name) const {
  int idx = find_inherited_rpc(name);
  if (idx != -1) {
    return _inherited_rpcs[idx];
  } else {
    return nullptr;
  }
}

/**
 *
 */
inline int NetworkClass::
find_inherited_rpc(const std::string &name) const {
  for (int i = (int)_inherited_rpcs.size() - 1; i >= 0; --i) {
    NetworkRPC *rpc = _inherited_rpcs[i];
    if (rpc->name == name) {
      return i;
    }
  }
  return -1;
}

/**
 *
 */
inline void NetworkClass::
set_stride(size_t stride) {
  _stride = stride;
}

/**
 *
 */
inline size_t NetworkClass::
get_stride() const {
  return _stride;
}

/**
 *
 */
template<typename Cls, typename Var>
constexpr size_t offset_of(Var Cls::*var) {
  return reinterpret_cast<size_t>(
    &(reinterpret_cast<Cls const volatile*>(0)->*var)
  );
}

/**
 *
 */
template<typename Cls, typename Var>
inline NetworkField *NetworkClass::
make_field(const std::string &name, Var Cls::*var) {
  using T = std::remove_cv_t<Var>;
  NetworkField *field = new NetworkField;
  field->name = name;
  field->source_type = NetworkFieldTypeTraits<T>::type;
  field->count = NetworkFieldTypeTraits<T>::count;
  field->stride = NetworkFieldTypeTraits<T>::stride;
  field->offset = offset_of(var);
  field->encoding_type = field->source_type;
  add_field(field);
  return field;
}

/**
 *
 */
template<typename Cls, typename Var>
inline NetworkField *NetworkClass::
make_field(const std::string &name, Var Cls::*var, NetworkField::DataType encoding_type, int divisor, float modulo) {
  NetworkField *field = make_field(name, var);
  field->encoding_type = encoding_type;
  field->divisor = divisor;
  field->modulo = modulo;
  return field;
}

/**
 *
 */
template<typename Var>
inline NetworkField *NetworkClass::
make_indirect_field(const std::string &name, NetworkField::IndirectFetchFunc fetch, NetworkField::IndirectWriteFunc write) {
  using T = std::remove_cv_t<Var>;
  NetworkField *field = new NetworkField;
  field->name = name;
  field->source_type = NetworkFieldTypeTraits<T>::type;
  field->encoding_type = NetworkFieldTypeTraits<T>::type;
  field->count = NetworkFieldTypeTraits<T>::count;
  field->stride = NetworkFieldTypeTraits<T>::stride;
  field->indirect_fetch = fetch;
  field->indirect_write = write;
  add_field(field);
  return field;
}

/**
 *
 */
template<typename Var>
inline NetworkField *NetworkClass::
make_indirect_field(const std::string &name, NetworkField::IndirectFetchFunc fetch, NetworkField::IndirectWriteFunc write, NetworkField::DataType encoding_type, int divisor, float modulo) {
  NetworkField *field = make_indirect_field<Var>(name, fetch, write);
  field->encoding_type = encoding_type;
  field->divisor = divisor;
  field->modulo = modulo;
  return field;
}

/**
 *
 */
template<typename Cls, typename Var>
inline NetworkField *NetworkClass::
make_struct_field(const std::string &name, Var Cls::*var, NetworkClass *struct_class) {
  using T = std::remove_cv_t<Var>;
  assert(sizeof(T) == struct_class->get_stride());
  NetworkField *field = new NetworkField;
  field->name = name;
  field->net_class = struct_class;
  field->source_type = NetworkField::DT_class;
  field->stride = struct_class->get_stride();
  field->offset = offset_of(var);
  add_field(field);
  return field;
}

/**
 *
 */
template<typename Var>
inline NetworkField *NetworkClass::
make_indirect_struct_field(const std::string &name, NetworkClass *struct_class, NetworkField::IndirectFetchFunc fetch, NetworkField::IndirectWriteFunc write) {
  using T = std::remove_cv_t<Var>;
  assert(sizeof(T) == struct_class->get_stride());
  NetworkField *field = new NetworkField;
  field->name = name;
  field->source_type = NetworkField::DT_class;
  field->net_class = struct_class;
  field->stride = struct_class->get_stride();
  field->indirect_fetch = fetch;
  field->indirect_write = write;
  add_field(field);
  return field;
}

#define MAKE_NET_FIELD(cls, var, ...) \
  _network_class->make_field<cls>(#var, &cls::var, __VA_ARGS__);

#define MAKE_STRUCT_NET_FIELD(cls, var, struct_cls) \
  _network_class->make_struct_field<cls>(#var, &cls::var, struct_cls);

#define MAKE_INDIRECT_NET_FIELD(type, field_name, fetch, write, ...) \
  _network_class->make_indirect_field<type>(#field_name, fetch, write, __VA_ARGS__);

#define MAKE_INDIRECT_STRUCT_NET_FIELD(type, field_name, struct_cls, fetch, write) \
  _network_class->make_indirect_struct_field<type>(#field_name, struct_cls, fetch, write);

#define MAKE_NET_RPC(rpc_name, rpc_class, rpc_flags, recv_func)	\
  { \
    NetworkRPC *rpc = new NetworkRPC; \
    rpc->name = #rpc_name; \
    rpc->net_class = rpc_class; \
    rpc->flags = rpc_flags; \
    rpc->recv = recv_func; \
    _network_class->add_rpc(rpc); \
  }

#define BEGIN_NET_FIELD(cls, var, ...) \
  { \
    NetworkField *field = MAKE_NET_FIELD(cls, var, __VA_ARGS__);
#define END_NET_FIELD() \
  }

#define BEGIN_INDIRECT_NET_FIELD(type, field_name, fetch, write, ...) \
  { \
    NetworkField *field = MAKE_INDIRECT_NET_FIELD(type, field_name, fetch, write, __VA_ARGS__);
#define END_INDIRECT_NET_FIELD() \
  }

#define BEGIN_STRUCT_NET_FIELD(cls, var, struct_cls) \
  { \
    NetworkField *field = MAKE_STRUCT_NET_FIELD(cls, var, struct_cls);
#define END_STRUCT_NET_FIELD() \
  }

#define BEGIN_INDIRECT_STRUCT_NET_FIELD(type, field_name, struct_cls, fetch, write) \
  { \
    NetworkField *field = MAKE_INDIRECT_STRUCT_NET_FIELD(type, field_name, struct_cls, fetch, write);
#define END_INDIRECT_STRUCT_NET_FIELD() \
  }

#define BEGIN_NETWORK_CLASS_NOBASE(cls) \
  if (_network_class != nullptr) return; \
  _network_class = new NetworkClass(#cls); \
  _network_class->set_stride(sizeof(cls));

#define BEGIN_NETWORK_CLASS(cls, parent) \
  BEGIN_NETWORK_CLASS_NOBASE(cls) \
  parent::init_network_class(); \
  _network_class->set_parent(parent::get_type_network_class()); \

#define END_NETWORK_CLASS() \
  NetworkClassRegistry::ptr()->register_class(_network_class);

#endif // NETWORKCLASS_H

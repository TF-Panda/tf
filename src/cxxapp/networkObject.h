#ifndef NETWORKOBJECT_H
#define NETWORKOBJECT_H

#include "referenceCount.h"
#include "genericAsyncTask.h"

#ifdef CLIENT
#include "client/client_config.h"
#include "interpolatedVariable.h"
#include "pointerTo.h"
/**
 *
 */
struct InterpolatedVarEntry {
  InterpolatedVariableBase *var;
  void *dest;
  unsigned int flags;
  bool needs_interpolation;
};
#endif

#ifdef SERVER
class ClientConnection;
#endif

class NetworkClass;

typedef uint32_t DO_ID;
typedef uint32_t ZONE_ID;

/**
 * Base class for a networked object.  This is like the DistributedObject in DIRECT.
 */
class NetworkObject : public ReferenceCount {
public:
  enum ObjectState {
    OS_new,
    OS_alive,
    OS_disabled,
  };

  inline NetworkObject();

  virtual NetworkClass *get_network_class() const=0;

  inline void set_do_id(DO_ID do_id);
  inline DO_ID get_do_id() const;

  inline void set_zone_id(ZONE_ID zone_id);
  inline ZONE_ID get_zone_id() const;

  virtual void pre_generate();
  virtual void generate();
  virtual void disable();

  inline bool is_do_new() const;
  inline bool is_do_alive() const;
  inline bool is_do_disabled() const;

  GenericAsyncTask *add_task(const std::string &name, GenericAsyncTask::TaskFunc func, int sort = 0);
  GenericAsyncTask *add_sim_task(const std::string &name, GenericAsyncTask::TaskFunc func, int sort = 0);
  void remove_task(const std::string &name);
  void remove_sim_task(const std::string &name);
  void remove_all_tasks();

#ifdef CLIENT
  enum InterpVarFlags {
    IVF_none = 0,
    IVF_simulation = 1 << 0,
    IVF_animation = 1 << 1,
    IVF_omit_update_last_networked = 1 << 2,
    IVF_exclude_auto_latch = 1 << 3,
    IVF_exclude_auto_interpolate = 1 << 4,
  };

  template<class Type>
  inline PT(InterpolatedVariable<Type>) make_interpolated_var(unsigned int flags = InterpVarFlags::IVF_simulation,
							      Type *data_ptr = nullptr,
							      typename InterpolatedVariable<Type>::GetValueFn getter = nullptr,
							      typename InterpolatedVariable<Type>::SetValueFn setter = nullptr);
  template<class Type>
  inline void make_interpolated_var(InterpolatedVariable<Type> *var, unsigned int flags = InterpVarFlags::IVF_simulation,
				    Type *data_ptr = nullptr,
				    typename InterpolatedVariable<Type>::GetValueFn getter = nullptr,
				    typename InterpolatedVariable<Type>::SetValueFn setter = nullptr);

  void record_values_for_interpolation(float time, unsigned int flags);
  void reset_interpolated_vars();
  void store_last_networked_value();

  virtual void pre_data_update();
  virtual void post_data_update();

  virtual void pre_interpolate();
  void interpolate(float time);
  virtual void post_interpolate();

  static void add_to_interp_list(NetworkObject *obj);
  static void remove_from_interp_list(NetworkObject *obj);
  static void interpolate_objects();

  inline void set_owner(bool flag);
  inline bool is_owner() const;
#endif

#ifdef SERVER
  inline void set_owner(ClientConnection *owner);
  inline ClientConnection *get_owner() const;
#endif

private:
  ObjectState _object_state;
  DO_ID _do_id;
  ZONE_ID _zone_id;
  // Object task stuff.
  typedef pflat_hash_map<std::string, PT(GenericAsyncTask), string_hash> TaskMap;
  TaskMap _tasks;
  TaskMap _sim_tasks;
#ifdef CLIENT
  typedef pvector<InterpolatedVarEntry> InterpolatedVars;
  InterpolatedVars _interp_vars;
  bool _predictable;
  float _last_interpolation_time;

  static pset<NetworkObject *> _interp_list;

  // Does our client own this object?
  bool _is_owner;
#endif
#ifdef SERVER
  ClientConnection *_owner;
#endif
};

/**
 *
 */
inline NetworkObject::
NetworkObject() :
  _do_id(0u),
  _zone_id(0u),
  _object_state(OS_new)
#ifdef CLIENT
  ,
  _predictable(false),
  _last_interpolation_time(0.0f),
  _is_owner(false)
#endif
#ifdef SERVER
  ,
  _owner(nullptr)
#endif
{
}

/**
 *
 */
inline void NetworkObject::
set_do_id(DO_ID do_id) {
  _do_id = do_id;
}

/**
 * Returns the shared network identifier for this object.  The distributed object ID.
 */
inline DO_ID NetworkObject::
get_do_id() const {
  return _do_id;
}

/**
 *
 */
inline void NetworkObject::
set_zone_id(ZONE_ID zone_id) {
  _zone_id = zone_id;
}

/**
 *
 */
inline ZONE_ID NetworkObject::
get_zone_id() const {
  return _zone_id;
}

/**
 * Returns true if the NetworkObject has been instantiated but isn't fully generated and
 * active yet.  This is before the initial state has been applied.
 */
inline bool NetworkObject::
is_do_new() const {
  return _object_state == OS_new;
}

/**
 * Return true if the NetworkObject is fully generated and active.  This will be after
 * the initial state has been applied and generate() was called.
 */
inline bool NetworkObject::
is_do_alive() const {
  return _object_state == OS_alive;
}

/**
 * Returns true if the NetworkObject has been disabled/deleted.
 */
inline bool NetworkObject::
is_do_disabled() const {
  return _object_state == OS_disabled;
}

#ifdef SERVER

/**
 *
 */
inline void NetworkObject::
set_owner(ClientConnection *owner) {
  _owner = owner;
}

/**
 *
 */
inline ClientConnection *NetworkObject::
get_owner() const {
  return _owner;
}

#endif

#ifdef CLIENT

/**
 *
 */
inline void NetworkObject::
set_owner(bool flag) {
  _is_owner = flag;
}

/**
 *
 */
inline bool NetworkObject::
is_owner() const {
  return _is_owner;
}

/**
 *
 */
template<class Type>
inline PT(InterpolatedVariable<Type>) NetworkObject::
make_interpolated_var(unsigned int flags, Type *data_ptr, typename InterpolatedVariable<Type>::GetValueFn getter,
		      typename InterpolatedVariable<Type>::SetValueFn setter) {
  PT(InterpolatedVariable<Type>) var = new InterpolatedVariable<Type>;
  make_interpolated_var(var, flags, data_ptr, getter, setter);
  return var;
}

/**
 *
 */
template<class Type>
inline void NetworkObject::
make_interpolated_var(InterpolatedVariable<Type> *var, unsigned int flags, Type *data_ptr,
		      typename InterpolatedVariable<Type>::GetValueFn getter,
		      typename InterpolatedVariable<Type>::SetValueFn setter) {
  var->set_data_ptr(data_ptr);
  var->set_getter_func(getter, this);
  var->set_setter_func(setter, this);
  var->set_interpolation_amount(get_client_interp_amount());
  InterpolatedVarEntry entry;
  entry.var = var;
  entry.flags = flags;
  entry.needs_interpolation = false;
  entry.dest = data_ptr;
  _interp_vars.push_back(std::move(entry));
}

#endif // CLIENT

#endif // NETWORKOBJECT_H

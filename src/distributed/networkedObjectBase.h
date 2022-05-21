/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkedObjectBase.h
 * @author brian
 * @date 2022-05-03
 */

#ifndef NETWORKEDOBJECTBASE_H
#define NETWORKEDOBJECTBASE_H

#include "tfbase.h"
#include "config_tfdistributed.h"
#include "typedReferenceCount.h"
#include "typeHandle.h"
#include "numeric_types.h"
#include "memoryBase.h"
#include "pmap.h"
#include "stl_compares.h"
#include "genericAsyncTask.h"

#define _CONCAT(x, y) x##y
#define CONCAT(x, y) _CONCAT(x, y)

#define NET_CLASS_DECL(clsname) \
  public: \
    static NetworkClass *_network_class; \
    static void init_network_class(); \
    virtual NetworkClass *get_network_class() const override { return clsname::_network_class; } \
    class CONCAT(clsname, _NetObjProxy) : public NetworkedObjectProxy { \
      public: \
        virtual TypeHandle get_object_type() const override { return clsname::_type_handle; } \
        virtual NetworkedObjectBase *make_object() const override { return new clsname; } \
        virtual NetworkClass *get_network_class() const override { return clsname::_network_class; } \
    };

#define NET_CLASS_DEF_BEGIN(clsname, baseclass) \
  NetworkClass *clsname::_network_class = nullptr; \
  void clsname::init_network_class() { \
    baseclass::init_network_class(); \
    if (_network_class == nullptr) { \
      _network_class = new NetworkClass(#clsname, sizeof(clsname)); \
      _network_class->set_linked_proxy(new CONCAT(clsname, _NetObjProxy)); \
      for (int i = 0; i < baseclass::_network_class->get_num_fields(); ++i) { \
        _network_class->add_field(baseclass::_network_class->get_field(i)); \
      }

#define NET_CLASS_DEF_BEGIN_NOBASE(clsname) \
  NetworkClass *clsname::_network_class = nullptr; \
  void clsname::init_network_class() { \
    if (_network_class == nullptr) { \
      _network_class = new NetworkClass(#clsname, sizeof(clsname)); \
      _network_class->set_linked_proxy(new CONCAT(clsname, _NetObjProxy));

#define NET_CLASS_DEF_END() \
      NetworkedObjectRegistry::get_global_ptr()->register_class(_network_class); \
    } \
  }

#define NET_OFFSET(type, var) (size_t)(&((type *)0)->var)

class NetworkedObjectBase;
class NetworkClass;

/**
 * The purpose of this class is to allow querying information about a
 * NetworkedObject type without needing a singleton of the NetworkedObject
 * itself.  Each NetworkedObject type inherits from this class and overrides
 * these virtual methods to return the correct things for that NetworkedObject
 * type.  A singleton is stored on NetworkClass to link NetworkClasses to
 * NetworkedObjects.
 */
class EXPCL_TF_DISTRIBUTED NetworkedObjectProxy : public MemoryBase {
public:
  virtual ~NetworkedObjectProxy() = default;
  virtual TypeHandle get_object_type() const = 0;
  virtual NetworkedObjectBase *make_object() const = 0;
  virtual NetworkClass *get_network_class() const = 0;
};

/**
 * Base class for any object that should be replicated over the network.
 */
class EXPCL_TF_DISTRIBUTED NetworkedObjectBase : public TypedReferenceCount {
  DECLARE_CLASS(NetworkedObjectBase, TypedReferenceCount);

PUBLISHED:
  INLINE NetworkedObjectBase();

  virtual ~NetworkedObjectBase() = default;

  enum LifeState : uint8_t {
    LS_deleted,
    LS_disabled,
    LS_fresh,
    LS_generated,
    LS_alive,
  };

  virtual void generate();
  virtual void announce_generate();
  virtual void disable();
  virtual void destroy();

  virtual void pre_data_update(bool generate);
  virtual void post_data_update(bool generate);

  INLINE void set_do_id(doid_t do_id);
  INLINE doid_t get_network_id() const;
  INLINE doid_t get_do_id() const;

  INLINE void set_zone_id(zoneid_t zone_id);
  INLINE zoneid_t get_zone_id() const;

  INLINE LifeState get_do_state() const;
  INLINE bool is_do_fresh() const;
  INLINE bool is_do_generated() const;
  INLINE bool is_do_alive() const;
  INLINE bool is_do_disabled() const;
  INLINE bool is_do_deleted() const;

  virtual NetworkClass *get_network_class() const = 0;

  // Task management.
  GenericAsyncTask *add_task(const std::string &name, GenericAsyncTask::TaskFunc *func,
                             int sort = 0);
  GenericAsyncTask *do_task_later(const std::string &name, GenericAsyncTask::TaskFunc *func,
                                  float delay, int sort = 0);
  GenericAsyncTask *add_sim_task(const std::string &name, GenericAsyncTask::TaskFunc *func,
                                 int sort = 0);
  GenericAsyncTask *do_sim_task_later(const std::string &name, GenericAsyncTask::TaskFunc *func,
                                      float delay, int sort = 0);
  GenericAsyncTask *get_task(const std::string &name) const;
  void remove_task(const std::string &name);
  void remove_all_tasks();

private:
  static void task_death(GenericAsyncTask *task, bool clean_exit, void *user_data);

protected:
  typedef pflat_hash_map<std::string, PT(GenericAsyncTask), string_hash> TaskMap;
  TaskMap _task_map;

  doid_t _network_id;
  zoneid_t _zone_id;
  LifeState _life_state;
};

#include "networkedObjectBase.I"

#endif // NETWORKEDOBJECTBASE_H

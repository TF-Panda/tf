/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file distributedObject.h
 * @author brian
 * @date 2022-05-18
 */

#ifndef DISTRIBUTEDOBJECT_H
#define DISTRIBUTEDOBJECT_H

#include "tfbase.h"
#include "networkedObjectBase.h"
#include "interpolatedVariable.h"
#include "weakPointerTo.h"
#include "pset.h"
#include "stl_compares.h"

/**
 * Base client DistributedObject view.  Implements interpolation.
 */
class DistributedObject : public NetworkedObjectBase {
  DECLARE_CLASS(DistributedObject, NetworkedObjectBase);

public:
  DistributedObject();

  virtual void disable() override;

  enum InterpVarFlags {
    IV_no_update_last_networked = 1 << 0,
    IV_no_auto_record = 1 << 1,
    IV_no_auto_interp = 1 << 2,
  };

  class InterpVarEntry {
  public:
    InterpVarEntry() = default;
    std::string _name;
    PT(InterpolatedVariableBase) _interp_var;
    void *_data;
    unsigned int _flags;
    bool _needs_interpolation;
  };

  typedef pflat_hash_set<WPT(DistributedObject), method_hash<WPT(DistributedObject) > > InterpList;

  void add_interpolated_var(InterpolatedVariableBase *var, void *data, const std::string &name, unsigned int flags = 0u);
  INLINE int get_num_interpolated_vars() const;
  INLINE InterpVarEntry *get_interpolated_var(int n);
  INLINE void remove_interpolated_var(int n);
  INLINE int find_interpolated_var(const std::string &name) const;
  INLINE int find_interpolated_var(const InterpolatedVariableBase *interp_var) const;
  INLINE int find_interpolated_var(void *data) const;

  bool interpolate(double time, bool remove_if_done = true);
  void record_interp_var_values(double timestamp, unsigned int flags);
  void store_last_networked_values();
  INLINE void add_to_interpolation_list();
  INLINE void remove_from_interpolation_list();

  virtual void pre_data_update(bool generate) override;
  virtual void post_data_update(bool generate) override;

  static void interpolate_objects(double time);
  INLINE static void clear_interp_list();

  virtual void post_interpolate();

  virtual bool is_predicted() const;

protected:
  typedef pvector<InterpVarEntry> InterpolatedVars;
  InterpolatedVars _interp_vars;

  static InterpList _interp_list;

  double _last_interp_time;
};

#include "distributedObject.I"

#endif // DISTRIBUTEDOBJECT_H

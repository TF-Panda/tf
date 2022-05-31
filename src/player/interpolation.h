/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file interpolation.h
 * @author brian
 * @date 2022-05-25
 */

#ifndef INTERPOLATION_H
#define INTERPOLATION_H

#include "tfbase.h"
#include "referenceCount.h"
#include "pset.h"
#include "stl_compares.h"
#include "interpolatedVariable.h"
#include "pointerTo.h"

/**
 * An object with a list of InterpolatedVariables that is linked back to
 * a Python object in show code.
 */
class InterpolatedObject {
PUBLISHED:
  class VarEntry {
  PUBLISHED:
    std::string _name;
    PT(InterpolatedVariableBase) _ivar;
    bool _needs_interpolation;
    unsigned int _flags;

    // We don't need to ref these since the InterpolatedObject's life is
    // dictated by the life of the object.
    PyObject *_setter;
    PyObject *_getter;
  };

  INLINE void add_to_interpolation_list();
  INLINE void remove_from_interpolation_list();

  INLINE void set_predicted(bool flag);
  INLINE bool is_predicted() const;

  static void interpolate_objects();
  INLINE static void clear_interp_list();

private:
  typedef pflat_hash_set<InterpolatedObject *, pointer_hash> InterpList;
  static InterpList _interp_list;

  bool _predicted;

  // We don't need to ref these since the InterpolatedObject's life is
  // dictated by the life of the object.
  PyObject *_py_obj;
  PyObject *_obj_dict;
};

#include "interpolation.I"

#endif // INTERPOLATION_H

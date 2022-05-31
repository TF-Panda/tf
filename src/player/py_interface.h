/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file py_interface.h
 * @author brian
 * @date 2022-05-25
 */

#ifndef PY_INTERFACE_H
#define PY_INTERFACE_H

#include "tfbase.h"
#include "py_panda.h"
#include "luse.h"

extern Dtool_PyTypedObject *py_vec2_type;
extern Dtool_PyTypedObject *py_vec3_type;
extern Dtool_PyTypedObject *py_vec4_type;
extern bool py_types_initialized;
INLINE void fetch_py_types();

INLINE PyObject *get_obj_dict(PyObject *obj);

INLINE PyObject *get_field_py_obj(PyObject *getter);
INLINE PyObject *get_field_py_obj(PyObject *dict, PyObject *field_name);

INLINE void set_field_py_obj(PyObject *setter, PyObject *value);
INLINE void set_field_py_obj(PyObject *dict, PyObject *field_name, PyObject *value);

INLINE void py_to_native(PyObject *args, int &native);
INLINE void py_to_native(PyObject *args, float &native);
INLINE void py_to_native(PyObject *args, bool &native);
INLINE void py_to_native(PyObject *args, LVecBase2f &native);
INLINE void py_to_native(PyObject *args, LVecBase3f &native);
INLINE void py_to_native(PyObject *args, LVecBase4f &native);

INLINE PyObject *py_from_native(int native);
INLINE PyObject *py_from_native(float native);
INLINE PyObject *py_from_native(bool native);
INLINE PyObject *py_from_native(const LVecBase2f &native);
INLINE PyObject *py_from_native(const LVecBase3f &native);
INLINE PyObject *py_from_native(const LVecBase4f &native);

#include "py_interface.I"

#endif // PY_INTERFACE_H

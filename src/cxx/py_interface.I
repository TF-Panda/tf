/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file py_interface.I
 * @author brian
 * @date 2022-05-25
 */

/**
 *
 */
INLINE void
fetch_py_types() {
  if (py_types_initialized) {
    return;
  }

  Dtool_TypeMap *tmap = Dtool_GetGlobalTypeMap();
  Dtool_TypeMap::const_iterator it;

  it = tmap->find("LVecBase2f");
  if (it != tmap->end()) {
    py_vec2_type = (*it).second;
  }

  it = tmap->find("LVecBase3f");
  if (it != tmap->end()) {
    py_vec3_type = (*it).second;
  }

  it = tmap->find("LVecBase4f");
  if (it != tmap->end()) {
    py_vec4_type = (*it).second;
  }

  py_types_initialized = true;
}

/**
 * Returns the instance dictionary of the indicated PyObject.
 */
INLINE PyObject *
get_obj_dict(PyObject *obj) {
  return PyObject_GetAttrString(obj, "__dict__");
}

/**
 * Extracts a field from a Python object by calling a getter method
 * that should return the field's value.
 */
INLINE PyObject *
get_field_py_obj(PyObject *getter) {
  return PyObject_CallNoArgs(getter);
}

/**
 * Extracts a field from a Python object by looking up into the object's
 * instance dictionary.
 */
INLINE PyObject *
get_field_py_obj(PyObject *dict, PyObject *field_name) {
  return PyDict_GetItem(dict, field_name);
}

/**
 * Sets a field on a Python object by calling a setter method that
 * should copy the passed in value onto the object.
 */
INLINE void
set_field_py_obj(PyObject *setter, PyObject *value) {
  PyObject *args = PyTuple_Pack(1, value);
  PyObject_CallObject(setter, args);
  Py_DECREF(args);
}

/**
 * Sets a field on a Python object by setting the field on the object's
 * instance dictionary.
 */
INLINE void
set_field_py_obj(PyObject *dict, PyObject *field_name, PyObject *value) {
  PyDict_SetItem(dict, field_name, value);
}

/**
 * Converts a numeric PyObject to a native int.
 */
INLINE void
py_to_native(PyObject *args, int &native) {
  native = (int)PyLong_AsLong(args);
}

/**
 * Converts a numeric PyObject to a native float.
 */
INLINE void
py_to_native(PyObject *args, float &native) {
  native = (float)PyFloat_AsDouble(args);
}

/**
 * Converts a PyObject to a native bool.
 */
INLINE void
py_to_native(PyObject *args, bool &native) {
  native = (bool)PyLong_AsLong(args);
}

/**
 * Converts a PyObject to an LVecBase2f.
 */
INLINE void
py_to_native(PyObject *args, LVecBase2f &native) {
  LVecBase2f *local_this;
  if (DtoolInstance_GetPointer(args, local_this, *PredictionCopy::_vec2_type)) {
    if (DtoolInstance_IS_CONST(args)) {
      // This is a const object.  Make a copy.
      coerced = *(const LVecBase2f *)local_this;
      return &coerced;
    }
    return local_this;
  }

  if (!PyTuple_Check(args)) {
    PyObject *arg = args;
    // 1-inline LVecBase2f::LVecBase2f(float fill_value)
    if (PyNumber_Check(arg)) {
      coerced = LVecBase2f((float)PyFloat_AsDouble(arg));
      if (_PyErr_OCCURRED()) {
        return nullptr;
      } else {
        return &coerced;
      }
    }
  } else {
    if (PyTuple_GET_SIZE(args) == 2) {
      // 1-inline LVecBase2f::LVecBase2f(float x, float y)
      float param0;
      float param1;
      if (PyArg_ParseTuple(args, "ff:LVecBase2f", &param0, &param1)) {
        coerced = LVecBase2f((float)param0, (float)param1);
        if (_PyErr_OCCURRED()) {
          return nullptr;
        } else {
          return &coerced;
        }
      }
      PyErr_Clear();
    }
  }

  return nullptr;
}


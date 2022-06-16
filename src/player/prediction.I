/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file prediction.I
 * @author brian
 * @date 2022-05-23
 */

/**
 *
 */
INLINE void PredictionField::
set_setter(PyObject *setter) {
  Py_XDECREF(_setter);
  _setter = setter;
  Py_XINCREF(_setter);
}

/**
 *
 */
INLINE PyObject *PredictionField::
get_setter() const {
  return _setter;
}

/**
 *
 */
INLINE void PredictionField::
set_getter(PyObject *getter) {
  Py_XDECREF(_getter);
  _getter = getter;
  Py_XINCREF(_getter);
}

/**
 *
 */
INLINE PyObject *PredictionField::
get_getter() const {
  return _getter;
}

/**
 *
 */
INLINE void PredictionField::
set_tolerance(float tolerance) {
  _tolerance = tolerance;
}

/**
 *
 */
INLINE float PredictionField::
get_tolerance() const {
  return _tolerance;
}

/**
 *
 */
INLINE void PredictionField::
set_flags(unsigned int flags) {
  _flags = flags;
}

/**
 *
 */
INLINE unsigned int PredictionField::
get_flags() const {
  return _flags;
}

/**
 * Returns the number of bytes taken up by the data for this field.
 */
INLINE size_t PredictionField::
get_stride() const {
  switch (_type) {
  case T_bool:
    return 1;
  case T_int:
  case T_float:
    return 4;
  case T_vec2:
    return 8;
  case T_vec3:
    return 12;
  case T_vec4:
    return 16;
  }
}

/**
 *
 */
INLINE PredictionField::Type PredictionField::
get_type() const {
  return _type;
}

/**
 *
 */
INLINE const std::string &PredictionField::
get_name() const {
  return _name;
}

/**
 *
 */
INLINE PyObject *PredictionField::
get_py_name() const {
  return _py_name;
}

/**
 *
 */
INLINE PredictionCopy::
PredictionCopy(CopyMode mode, PredictedObject *obj, PTA_uchar dest_dict, PTA_uchar src_dict,
               bool count_errors, bool report_errors, bool perform_copy) :
  _mode(mode),
  _error_check(count_errors),
  _perform_copy(perform_copy),
  _report_errors(report_errors),
  _error_count(0),
  _src_dist(src_dict),
  _dest_dict(dest_dict),
  _obj(obj),
  _current_command_reference(0),
  _dest_slot(0),
  _cmd_num(0)
{
}

/**
 * Template method for comparing two linmath vectors.
 */
template<class Type>
INLINE PredictionCopy::DiffType PredictionCopy::
compare_vecs(const Type &a, const Type &b, float tolerance) {
  DiffType diff = DT_identical;
  bool differs = (a != b);
  if (differs && tolerance > 0.0f) {
    Type delta = b - a;
    diff = DT_within_tolerance;
    for (int i = 0; i < Type::num_components; ++i) {
      if (cabs(delta[i]) > tolerance) {
        diff = DT_differs;
        break;
      }
    }
  } else if (differs) {
    diff = DT_differs;
  }

  return diff;
}

/**
 *
 */
template<class Type>
INLINE void PredictionCopy::
report_error_delta(const PredictionField *field, int cmd, const Type &predicted, const Type &received) {
  prediction_cat.info()
    << field->get_name() << " differs (command " << cmd << "): pred "
    << predicted << ", net " << received << ", delta " << received - predicted << "\n";
}

/**
 *
 */
template<class Type>
INLINE void PredictionCopy::
report_error(const PredictionField *field, int cmd, const Type &predicted, const Type &received) {
  prediction_cat.info()
    << field->get_name() << " differs (command " << cmd << "): pred "
    << predicted << ", net " << received << "\n";
}

/**
 *
 */
INLINE PyObject *PredictionCopy::
get_field_py_obj(const PredictionField *field) {
  PyObject *py_obj;
  if (field->get_getter() != nullptr) {
    py_obj = PyObject_CallNoArgs(field->get_getter());
  } else {
    py_obj = PyDict_GetItem(_obj->_dict, field->get_py_name());
    Py_XINCREF(py_obj);
  }
  return py_obj;
}

/**
 *
 */
INLINE void PredictionCopy::
set_field_py_obj(const PredictionField *field, PyObject *obj) {
  if (field->get_setter() != nullptr) {
    PyObject *args = PyTuple_Pack(1, obj);
    PyObject_CallObject(field->get_setter(), args);
    Py_DECREF(args);
  } else {
    PyDict_SetItem(_obj->_dict, field->get_py_name(), obj);
  }
  Py_DECREF(obj);
}

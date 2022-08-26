/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file prediction.cxx
 * @author brian
 * @date 2022-05-23
 */

#include "prediction.h"
#include "pStatCollector.h"
#include "pStatTimer.h"

#include <xutility>

static PStatCollector transfer_pcollector("PredictionCPP:TransferData");
static PStatCollector shift_pcollector("PredictionCPP:ShiftIntermediateDataForward");
static PStatCollector alloc_pcollector("PredictionCPP:AllocSlot");

NotifyCategoryDef(prediction, "");

PredictionField::
PredictionField() :
  _getter(nullptr),
  _setter(nullptr),
  _py_name(nullptr)
{
}

/**
 *
 */
PredictionField::
PredictionField(const std::string &name, Type type, unsigned int flags) :
  _name(name),
  _type(type),
  _getter(nullptr),
  _setter(nullptr),
  _flags(flags),
  _tolerance(0.0f)
{
  _py_name = PyUnicode_FromString(name.c_str());
}

/**
 *
 */
PredictionField::
PredictionField(const PredictionField &copy) :
  _name(copy._name),
  _type(copy._type),
  _getter(copy._getter),
  _setter(copy._setter),
  _flags(copy._flags),
  _tolerance(copy._tolerance),
  _py_name(copy._py_name)
{
  Py_XINCREF(_py_name);
  Py_XINCREF(_getter);
  Py_XINCREF(_setter);
}

/**
 *
 */
PredictionField::
PredictionField(PredictionField &&other) :
  _name(other._name),
  _type(other._type),
  _getter(other._getter),
  _setter(other._setter),
  _flags(other._flags),
  _tolerance(other._tolerance),
  _py_name(other._py_name)
{
  other._getter = nullptr;
  other._setter = nullptr;
  other._py_name = nullptr;
}

/**
 *
 */
PredictionField::
~PredictionField() {
  Py_CLEAR(_py_name);
  Py_CLEAR(_getter);
  Py_CLEAR(_setter);
}

/**
 *
 */
PredictionField &PredictionField::
operator = (const PredictionField &copy) {
  _name = copy._name;
  _type = copy._type;
  if (_getter != copy._getter) {
    Py_XDECREF(_getter);
    _getter = copy._getter;
    Py_XINCREF(_getter);
  }
  if (_setter != copy._setter) {
    Py_XDECREF(_setter);
    _setter = copy._setter;
    Py_XINCREF(_setter);
  }
  _flags = copy._flags;
  _tolerance = copy._tolerance;
  if (_py_name != copy._py_name) {
    Py_XDECREF(_py_name);
    _py_name = copy._py_name;
    Py_XINCREF(_py_name);
  }
  return *this;
}

/**
 *
 */
PredictionField &PredictionField::
operator = (PredictionField &&other) {
  _name = other._name;
  _type = other._type;
  if (_getter != other._getter) {
    Py_XDECREF(_getter);
  }
  _getter = other._getter;
  if (_setter != other._setter) {
    Py_XDECREF(_setter);
  }
  _setter = other._setter;
  _flags = other._flags;
  _tolerance = other._tolerance;
  if (_py_name != other._py_name) {
    Py_XDECREF(_py_name);
  }
  _py_name = other._py_name;
  other._py_name = nullptr;
  other._getter = nullptr;
  other._setter = nullptr;
  return *this;
}

/**
 *
 */
void PredictionField::
cleanup() {
  Py_CLEAR(_py_name);
  Py_CLEAR(_getter);
  Py_CLEAR(_setter);
}

/**
 * xyz
 */
PredictedObject::
PredictedObject(PyObject *py_entity) :
  _py_entity(py_entity),
  _intermediate_data_count(0),
  _buffer_size(0u),
  _dict(nullptr)
{
  _dict = PyObject_GetAttrString(_py_entity, "__dict__");
  nassertv(_dict != nullptr && PyDict_Check(_dict));
}

/**
 * xyz
 */
PredictedObject::
~PredictedObject() {
  // cleanup() should have been called before destruction to
  // release references.
  Py_CLEAR(_dict);
}

/**
 *
 */
void PredictedObject::
cleanup() {
  for (PredictionField &field : _fields) {
    field.cleanup();
  }
  _fields.clear();
  _original_data.clear();
  for (int i = 0; i < prediction_data_slots; ++i) {
    _data_slots[i].clear();
  }
  Py_CLEAR(_dict);
  _py_entity = nullptr;
}

/**
 *
 */
void PredictedObject::
add_field(const PredictionField &field) {
  PredictionFields::iterator it = std::find_if(_fields.begin(), _fields.end(),
    [field] (const PredictionField &other) {
      return field.get_name() == other.get_name();
    }
  );
  if (it != _fields.end()) {
    // Replace field with same name.
    (*it) = field;
  } else {
    _fields.push_back(field);
  }

}

/**
 *
 */
void PredictedObject::
remove_field(const std::string &name) {
  PredictionFields::const_iterator it = std::find_if(_fields.begin(), _fields.end(),
    [name] (const PredictionField &field) {
      return field.get_name() == name;
    }
  );
  if (it != _fields.end()) {
    _fields.erase(it);
  }
}

/**
 *
 */
int PredictedObject::
save_data(int slot, PredictionCopy::CopyMode type) {
  PTA_uchar dest = alloc_slot(slot);
  if (slot != -1) {
    _intermediate_data_count = slot;
  }
  PredictionCopy copy(type, this, dest, PTA_uchar());
  return copy.transfer_data();
}

/**
 *
 */
int PredictedObject::
restore_data(int slot, PredictionCopy::CopyMode type) {
  PTA_uchar src = alloc_slot(slot);
  PredictionCopy copy(type, this, PTA_uchar(), src);
  return copy.transfer_data();
}

/**
 *
 */
void PredictedObject::
shift_intermediate_data_forward(int slots_to_remove, int num_cmds_run) {
  PStatTimer timer(shift_pcollector);

  nassertv(num_cmds_run >= slots_to_remove);

  pvector<PTA_uchar> saved;
  saved.reserve(slots_to_remove);

  int i = 0;
  // Remember first slots.
  while (i < slots_to_remove) {
    saved.push_back(_data_slots[i]);
    ++i;
  }
  // Move rest of slots forward up to last slot.
  while (i < num_cmds_run) {
    _data_slots[i - slots_to_remove] = _data_slots[i];
    ++i;
  }
  // Put remembered slots onto end.
  for (i = 0; i < slots_to_remove; ++i) {
    int slot = num_cmds_run - slots_to_remove + i;
    _data_slots[slot] = saved[i];
  }
}

/**
 *
 */
void PredictedObject::
pre_entity_packet_received(int commands_acked) {
  bool copy_intermediate = (commands_acked > 0);

  if (copy_intermediate) {
    restore_data(commands_acked - 1, PredictionCopy::CM_non_networked_only);
    restore_data(-1, PredictionCopy::CM_networked_only);
  } else {
    restore_data(-1, PredictionCopy::CM_everything);
  }
}

/**
 *
 */
void PredictedObject::
post_entity_packet_received() {
  save_data(-1, PredictionCopy::CM_networked_only);
}

/**
 *
 */
bool PredictedObject::
post_network_data_received(int commands_acked, int curr_reference) {
  bool had_errors = false;
  bool error_check = (commands_acked > 0);

  save_data(-1, PredictionCopy::CM_everything);

  if (error_check) {
    PTA_uchar predicted_state_data = alloc_slot(commands_acked - 1);
    PTA_uchar original_state_data = alloc_slot(-1);
    bool count_errors = true;
    bool copy_data = false;
    PredictionCopy copy(PredictionCopy::CM_networked_only, this, predicted_state_data, original_state_data,
                        count_errors, true, copy_data);
    int error_count = copy.transfer_data(curr_reference, commands_acked - 1);
    if (error_count > 0) {
      had_errors = true;
    }
  }

  return had_errors;
}

/**
 * Allocates an intermediate result buffer at the indicated slot, and returns
 * the buffer.
 */
PTA_uchar PredictedObject::
alloc_slot(int slot) {
  PStatTimer timer(alloc_pcollector);

  nassertr(slot >= -1, PTA_uchar());

  if (slot == -1) {
    if (_original_data.is_null()) {
      _original_data.resize(_buffer_size);
      memset(_original_data.p(), 0, _buffer_size);
    }
    return _original_data;

  } else {
    slot = slot % prediction_data_slots;
    if (_data_slots[slot].is_null()) {
      _data_slots[slot].resize(_buffer_size);
      memset(_data_slots[slot].p(), 0, _buffer_size);
    }
    return _data_slots[slot];
  }
}

/**
 *
 */
void PredictedObject::
calc_buffer_size() {
  _buffer_size = 0u;
  for (size_t i = 0; i < _fields.size(); ++i) {
    _buffer_size += _fields[i].get_stride();
  }
}

bool PredictionCopy::_got_types = false;
Dtool_PyTypedObject *PredictionCopy::_vec2_type = nullptr;
Dtool_PyTypedObject *PredictionCopy::_vec3_type = nullptr;
Dtool_PyTypedObject *PredictionCopy::_vec4_type = nullptr;

/**
 * Function to construct an LVecBase2f from a Python object.
 *
 * Copied from interrogate-generated code.
 */
static LVecBase2f *Dtool_Coerce_LVecBase2f(PyObject *args, LVecBase2f &coerced) {
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

/**
 * Function to construct an LVecBase3f from a Python object.
 *
 * Copied from interrogate-generated code.
 */
static LVecBase3f *Dtool_Coerce_LVecBase3f(PyObject *args, LVecBase3f &coerced) {
  LVecBase3f *local_this;
  if (DtoolInstance_GetPointer(args, local_this, *PredictionCopy::_vec3_type)) {
    if (DtoolInstance_IS_CONST(args)) {
      // This is a const object.  Make a copy.
      coerced = *(const LVecBase3f *)local_this;
      return &coerced;
    }
    return local_this;
  }

  if (!PyTuple_Check(args)) {
    PyObject *arg = args;
    // 1-inline LVecBase3f::LVecBase3f(float fill_value)
    if (PyNumber_Check(arg)) {
      coerced = LVecBase3f((float)PyFloat_AsDouble(arg));
      if (_PyErr_OCCURRED()) {
        return nullptr;
      } else {
        return &coerced;
      }
    }
  } else {
    switch (PyTuple_GET_SIZE(args)) {
      case 3: {
        // 1-inline LVecBase3f::LVecBase3f(float x, float y, float z)
        float param0;
        float param1;
        float param2;
        if (PyArg_ParseTuple(args, "fff:LVecBase3f", &param0, &param1, &param2)) {
          coerced = LVecBase3f((float)param0, (float)param1, (float)param2);
          if (_PyErr_OCCURRED()) {
            return nullptr;
          } else {
            return &coerced;
          }
        }
        PyErr_Clear();
        break;
      }
    }
  }

  return nullptr;
}

/**
 * Function to construct an LVecBase4f from a Python object.
 *
 * Copied from interrogate-generated code.
 */
static LVecBase4f *Dtool_Coerce_LVecBase4f(PyObject *args, LVecBase4f &coerced) {
  LVecBase4f *local_this;
  if (DtoolInstance_GetPointer(args, local_this, *PredictionCopy::_vec4_type)) {
    if (DtoolInstance_IS_CONST(args)) {
      // This is a const object.  Make a copy.
      coerced = *(const LVecBase4f *)local_this;
      return &coerced;
    }
    return local_this;
  }

  if (!PyTuple_Check(args)) {
    PyObject *arg = args;
    {
      // -2 inline LVecBase4f::LVecBase4f(float fill_value)
      if (PyNumber_Check(arg)) {
        coerced = LVecBase4f((float)PyFloat_AsDouble(arg));
        if (_PyErr_OCCURRED()) {
          return nullptr;
        } else {
          return &coerced;
        }
      }
    }
  } else {
    switch (PyTuple_GET_SIZE(args)) {
      case 4: {
        // 1-inline LVecBase4f::LVecBase4f(float x, float y, float z, float w)
        float param0;
        float param1;
        float param2;
        float param3;
        if (PyArg_ParseTuple(args, "ffff:LVecBase4f", &param0, &param1, &param2, &param3)) {
          coerced = LVecBase4f((float)param0, (float)param1, (float)param2, (float)param3);
          if (_PyErr_OCCURRED()) {
            return nullptr;
          } else {
            return &coerced;
          }
        }
        PyErr_Clear();
        break;
      }
    }
  }

  return nullptr;
}

/**
 *
 */
int PredictionCopy::
transfer_data(int current_command_reference, int dest_slot) {
  PStatTimer timer(transfer_pcollector);

  if (!_got_types) {
    fetch_types();
  }

  _current_command_reference = current_command_reference;
  _dest_slot = dest_slot;
  _cmd_num = _current_command_reference + _dest_slot;

  size_t pos = 0u;
  for (size_t i = 0; i < _obj->_fields.size(); ++i) {
    const PredictionField *field = &_obj->_fields[i];
    if ((field->get_flags() & PredictionField::F_private) != 0) {
      pos += field->get_stride();
      continue;
    }
    if (_mode == CM_non_networked_only && (field->get_flags() & PredictionField::F_networked) != 0) {
      pos += field->get_stride();
      continue;
    }
    if (_mode == CM_networked_only && (field->get_flags() & PredictionField::F_networked) == 0) {
      pos += field->get_stride();
      continue;
    }
    DiffType diff = transfer_field(field, pos);

    // Advance position in intermediate result buffer.
    pos += field->get_stride();
  }

  return _error_count;
}

/**
 *
 */
PredictionCopy::DiffType PredictionCopy::
transfer_field(const PredictionField *field, size_t pos) {
  DiffType diff = DT_differs;

  if (field->get_type() == PredictionField::T_int) {
    int src_value = get_int_value(field, _src_dist, pos);
    int dest_value = get_int_value(field, _dest_dict, pos);

    if (_error_check) {
      diff = compare_ints(src_value, dest_value);
    }

    if (_perform_copy && diff != DT_identical) {
      set_int_value(src_value, field, _dest_dict, pos);
    }

    if (_error_check && diff == DT_differs) {
      if (_report_errors) {
        report_error_delta(field, _cmd_num, src_value, dest_value);
      }
      ++_error_count;
    }

  } else if (field->get_type() == PredictionField::T_bool) {
    bool src_value = get_bool_value(field, _src_dist, pos);
    bool dest_value = get_bool_value(field, _dest_dict, pos);

    if (_error_check) {
      diff = compare_bools(src_value, dest_value);
    }

    if (_perform_copy && diff != DT_identical) {
      set_bool_value(src_value, field, _dest_dict, pos);
    }

    if (_error_check && diff == DT_differs) {
      if (_report_errors) {
        report_error(field, _cmd_num, src_value, dest_value);
      }
      ++_error_count;
    }

  } else if (field->get_type() == PredictionField::T_float) {
    float src_value = get_float_value(field, _src_dist, pos);
    float dest_value = get_float_value(field, _dest_dict, pos);

    if (_error_check) {
      diff = compare_floats(src_value, dest_value, field->get_tolerance());
    }

    if (_perform_copy && diff != DT_identical) {
      set_float_value(src_value, field, _dest_dict, pos);
    }

    if (_error_check && diff == DT_differs) {
      if (_report_errors) {
        report_error_delta(field, _cmd_num, src_value, dest_value);
      }
      ++_error_count;
    }

  } else if (field->get_type() == PredictionField::T_vec2) {
    LVecBase2f src_value = get_vec2_value(field, _src_dist, pos);
    LVecBase2f dest_value = get_vec2_value(field, _dest_dict, pos);

    if (_error_check) {
      diff = compare_vecs(src_value, dest_value, field->get_tolerance());
    }

    if (_perform_copy && diff != DT_identical) {
      set_vec2_value(src_value, field, _dest_dict, pos);
    }

    if (_error_check && diff == DT_differs) {
      if (_report_errors) {
        report_error_delta(field, _cmd_num, src_value, dest_value);
      }
      ++_error_count;
    }

  } else if (field->get_type() == PredictionField::T_vec3) {
    LVecBase3f src_value = get_vec3_value(field, _src_dist, pos);
    LVecBase3f dest_value = get_vec3_value(field, _dest_dict, pos);

    if (_error_check) {
      diff = compare_vecs(src_value, dest_value, field->get_tolerance());
    }

    if (_perform_copy && diff != DT_identical) {
      set_vec3_value(src_value, field, _dest_dict, pos);
    }

    if (_error_check && diff == DT_differs) {
      if (_report_errors) {
        report_error_delta(field, _cmd_num, src_value, dest_value);
      }
      ++_error_count;
    }

  } else if (field->get_type() == PredictionField::T_vec4) {
    LVecBase4f src_value = get_vec4_value(field, _src_dist, pos);
    LVecBase4f dest_value = get_vec4_value(field, _dest_dict, pos);

    if (_error_check) {
      diff = compare_vecs(src_value, dest_value, field->get_tolerance());
    }

    if (_perform_copy && diff != DT_identical) {
      set_vec4_value(src_value, field, _dest_dict, pos);
    }

    if (_error_check && diff == DT_differs) {
      if (_report_errors) {
        report_error_delta(field, _cmd_num, src_value, dest_value);
      }
      ++_error_count;
    }
  }

  return diff;
}

/**
 *
 */
int PredictionCopy::
get_int_value(const PredictionField *field, const PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    return *(int *)(dict.p() + pos);
  } else {
    PyObject *int_obj = get_field_py_obj(field);
    int value = (int)PyLong_AsLong(int_obj);
    Py_DECREF(int_obj);
    return value;
  }
}

/**
 *
 */
void PredictionCopy::
set_int_value(int value, const PredictionField *field, PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    *(int *)(dict.p() + pos) = value;
  } else {
    set_field_py_obj(field, PyLong_FromLong((long)value));
  }
}

/**
 *
 */
PredictionCopy::DiffType PredictionCopy::
compare_ints(int a, int b) {
  if (a != b) {
    return DT_differs;
  }
  return DT_identical;
}

/**
 *
 */
bool PredictionCopy::
get_bool_value(const PredictionField *field, const PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    return *(bool *)(dict.p() + pos);
  } else {
    PyObject *bool_obj = get_field_py_obj(field);
    bool value = (bool)PyLong_AsLong(bool_obj);
    Py_DECREF(bool_obj);
    return value;
  }
}

/**
 *
 */
void PredictionCopy::
set_bool_value(bool value, const PredictionField *field, PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    *(bool *)(dict.p() + pos) = value;
  } else {
    set_field_py_obj(field, PyBool_FromLong((long)value));
  }
}

/**
 *
 */
PredictionCopy::DiffType PredictionCopy::
compare_bools(bool a, bool b) {
  if (a != b) {
    return DT_differs;
  }
  return DT_identical;
}

/**
 *
 */
float PredictionCopy::
get_float_value(const PredictionField *field, const PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    return *(float *)(dict.p() + pos);
  } else {
    PyObject *flt_obj = get_field_py_obj(field);
    float value = (float)PyFloat_AsDouble(flt_obj);
    Py_DECREF(flt_obj);
    return value;
  }
}

/**
 *
 */
void PredictionCopy::
set_float_value(float value, const PredictionField *field, PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    *(float *)(dict.p() + pos) = value;
  } else {
    set_field_py_obj(field, PyFloat_FromDouble((double)value));
  }
}

/**
 *
 */
PredictionCopy::DiffType PredictionCopy::
compare_floats(float a, float b, float tolerance) {
  if (a == b) {
    return DT_identical;

  } else if (tolerance > 0.0f && cabs(b - a) <= tolerance) {
    return DT_within_tolerance;

  } else {
    return DT_differs;
  }
}

/**
 *
 */
LVecBase2f PredictionCopy::
get_vec2_value(const PredictionField *field, const PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    float *data = (float *)(dict.p() + pos);
    return LVecBase2f(data[0], data[1]);
  } else {
    PyObject *vec_obj = get_field_py_obj(field);
    LVecBase2f tmp;
    LVecBase2f *coerced = Dtool_Coerce_LVecBase2f(vec_obj, tmp);
    tmp = *coerced;
    Py_DECREF(vec_obj);
    nassertr(coerced != nullptr, LVecBase2f());
    return tmp;
  }
}

/**
 *
 */
void PredictionCopy::
set_vec2_value(const LVecBase2f &value, const PredictionField *field,
               PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    float *data = (float *)(dict.p() + pos);
    data[0] = value[0];
    data[1] = value[1];

  } else {
    LVecBase2f *vec = new LVecBase2f(value);
    set_field_py_obj(field, DTool_CreatePyInstance((void *)vec, *_vec2_type, true, false));
  }
}

/**
 *
 */
LVecBase3f PredictionCopy::
get_vec3_value(const PredictionField *field, const PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    float *data = (float *)(dict.p() + pos);
    return LVecBase3f(data[0], data[1], data[2]);
  } else {
    PyObject *vec_obj = get_field_py_obj(field);
    LVecBase3f tmp;
    LVecBase3f *coerced = Dtool_Coerce_LVecBase3f(vec_obj, tmp);
    tmp = *coerced;
    Py_DECREF(vec_obj);
    nassertr(coerced != nullptr, LVecBase3f());
    return tmp;
  }
}

/**
 *
 */
void PredictionCopy::
set_vec3_value(const LVecBase3f &value, const PredictionField *field,
               PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    float *data = (float *)(dict.p() + pos);
    data[0] = value[0];
    data[1] = value[1];
    data[2] = value[2];

  } else {
    LVecBase3f *vec = new LVecBase3f(value);
    set_field_py_obj(field, DTool_CreatePyInstance((void *)vec, *_vec3_type, true, false));
  }
}

/**
 *
 */
LVecBase4f PredictionCopy::
get_vec4_value(const PredictionField *field, const PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    float *data = (float *)(dict.p() + pos);
    return LVecBase4f(data[0], data[1], data[2], data[3]);
  } else {
    PyObject *vec_obj = get_field_py_obj(field);
    LVecBase4f tmp;
    LVecBase4f *coerced = Dtool_Coerce_LVecBase4f(vec_obj, tmp);
    tmp = *coerced;
    Py_DECREF(vec_obj);
    nassertr(coerced != nullptr, LVecBase4f());
    return tmp;
  }
}

/**
 *
 */
void PredictionCopy::
set_vec4_value(const LVecBase4f &value, const PredictionField *field,
               PTA_uchar &dict, size_t pos) {
  if (!dict.is_null()) {
    float *data = (float *)(dict.p() + pos);
    data[0] = value[0];
    data[1] = value[1];
    data[2] = value[2];
    data[3] = value[3];

  } else {
    LVecBase4f *vec = new LVecBase4f(value);
    set_field_py_obj(field, DTool_CreatePyInstance((void *)vec, *_vec4_type, true, false));
  }
}

/**
 *
 */
void PredictionCopy::
fetch_types() {
  Dtool_TypeMap *tmap = Dtool_GetGlobalTypeMap();
  Dtool_TypeMap::const_iterator it;

  it = tmap->find("LVecBase2f");
  if (it != tmap->end()) {
    _vec2_type = (*it).second;
  }

  it = tmap->find("LVecBase3f");
  if (it != tmap->end()) {
    _vec3_type = (*it).second;
  }

  it = tmap->find("LVecBase4f");
  if (it != tmap->end()) {
    _vec4_type = (*it).second;
  }

  _got_types = true;
}

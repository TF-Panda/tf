/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file prediction.h
 * @author brian
 * @date 2022-05-23
 */

#ifndef PREDICTION_H
#define PREDICTION_H

/**
 * Implements prediction data storage and transfer in C++ for efficiency
 * reasons.
 */

#include "tfbase.h"
#include "py_panda.h"
#include "pta_uchar.h"
#include "luse.h"
#include "cmath.h"
#include "namable.h"
#include "referenceCount.h"
#include "pointerTo.h"
#include "notifyCategoryProxy.h"

NotifyCategoryDeclNoExport(prediction);

#ifdef CPPPARSER
class Dtool_PyTypedObject;
#endif

/**
 *
 */
class PredictionField {
PUBLISHED:
  enum Type {
    T_int,
    T_float,
    T_bool,
    T_vec2,
    T_vec3,
    T_vec4,
  };

  enum Flags {
    F_private = 1 << 0,
    F_networked = 1 << 1,
    F_no_error_check = 1 << 2,
  };

  PredictionField();
  PredictionField(const std::string &name, Type type, unsigned int flags);
  PredictionField(const PredictionField &copy);
  PredictionField(PredictionField &&other);
  ~PredictionField();

  PredictionField &operator = (const PredictionField &copy);
  PredictionField &operator = (PredictionField &&other);

  void cleanup();

  INLINE void set_setter(PyObject *setter);
  INLINE PyObject *get_setter() const;

  INLINE void set_getter(PyObject *getter);
  INLINE PyObject *get_getter() const;

  INLINE void set_tolerance(float tolerance);
  INLINE float get_tolerance() const;

  INLINE void set_flags(unsigned int flags);
  INLINE unsigned int get_flags() const;

  INLINE size_t get_stride() const;
  INLINE Type get_type() const;
  INLINE const std::string &get_name() const;
  INLINE PyObject *get_py_name() const;

  MAKE_PROPERTY(setter, get_setter, set_setter);
  MAKE_PROPERTY(getter, get_getter, set_getter);
  MAKE_PROPERTY(tolerance, get_tolerance, set_tolerance);
  MAKE_PROPERTY(flags, get_flags, set_flags);
  MAKE_PROPERTY(type, get_type);
  MAKE_PROPERTY(stride, get_stride);
  MAKE_PROPERTY(name, get_name);

private:
  std::string _name;
  PyObject *_py_name;

  Type _type;

  PyObject *_setter;
  PyObject *_getter;

  unsigned int _flags;
  float _tolerance;
};
typedef pvector<PredictionField> PredictionFields;

static const int prediction_data_slots = 90;

class PredictedObject;

/**
 *
 */
class PredictionCopy {
PUBLISHED:
  enum CopyMode {
    CM_everything,
    CM_non_networked_only,
    CM_networked_only,
  };

  enum DiffType {
    DT_differs,
    DT_identical,
    DT_within_tolerance,
  };

  INLINE PredictionCopy(CopyMode mode, PredictedObject *obj, PTA_uchar dest_dict,
                        PTA_uchar src_dict, bool count_errors = false,
                        bool report_errors = false, bool perform_copy = true);

  int transfer_data(int current_command_reference = -1, int dest_slot = -1);
  DiffType transfer_field(const PredictionField *field, size_t pos);

  //
  // Getter/setter/comparison for different data types.
  //

  int get_int_value(const PredictionField *field, const PTA_uchar &dict, size_t pos);
  void set_int_value(int value, const PredictionField *field, PTA_uchar &dict, size_t pos);
  DiffType compare_ints(int a, int b);

  bool get_bool_value(const PredictionField *field, const PTA_uchar &dict, size_t pos);
  void set_bool_value(bool value, const PredictionField *field, PTA_uchar &dict, size_t pos);
  DiffType compare_bools(bool a, bool b);

  float get_float_value(const PredictionField *field, const PTA_uchar &dict, size_t pos);
  void set_float_value(float value, const PredictionField *field, PTA_uchar &dict, size_t pos);
  DiffType compare_floats(float a, float b, float tolerance);

  LVecBase2f get_vec2_value(const PredictionField *field, const PTA_uchar &dict, size_t pos);
  void set_vec2_value(const LVecBase2f &value, const PredictionField *field, PTA_uchar &dict, size_t pos);

  LVecBase3f get_vec3_value(const PredictionField *field, const PTA_uchar &dict, size_t pos);
  void set_vec3_value(const LVecBase3f &value, const PredictionField *field, PTA_uchar &dict, size_t pos);

  LVecBase4f get_vec4_value(const PredictionField *field, const PTA_uchar &dict, size_t pos);
  void set_vec4_value(const LVecBase4f &value, const PredictionField *field, PTA_uchar &dict, size_t pos);

  template<class Type>
  INLINE DiffType compare_vecs(const Type &a, const Type &b, float tolerance);

  template<class Type>
  INLINE void report_error_delta(const PredictionField *field, int cmd, const Type &predicted_value, const Type &received_value);
  template<class Type>
  INLINE void report_error(const PredictionField *field, int cmd, const Type &predicted, const Type &received);

  INLINE PyObject *get_field_py_obj(const PredictionField *field);
  INLINE void set_field_py_obj(const PredictionField *field, PyObject *obj);

public:
  static bool _got_types;
  static Dtool_PyTypedObject *_vec2_type;
  static Dtool_PyTypedObject *_vec3_type;
  static Dtool_PyTypedObject *_vec4_type;

  static void fetch_types();

  CopyMode _mode;

  bool _error_check;
  bool _perform_copy;
  bool _report_errors;

  int _dest_slot;
  int _current_command_reference;
  int _cmd_num;

  int _error_count;

  PTA_uchar _src_dist, _dest_dict;
  PredictedObject *_obj;
};

/**
 *
 */
class PredictedObject {
PUBLISHED:
  PredictedObject(PyObject *py_entity);
  ~PredictedObject();

  void cleanup();

  void add_field(const PredictionField &field);
  void remove_field(const std::string &name);

  int save_data(int slot, PredictionCopy::CopyMode type);
  int restore_data(int slot, PredictionCopy::CopyMode type);
  void shift_intermediate_data_forward(int slots_to_remove, int num_cmds_run);
  void pre_entity_packet_received(int commands_acked);
  void post_entity_packet_received();
  bool post_network_data_received(int commands_acked, int curr_reference);

  PTA_uchar alloc_slot(int slot);
  void calc_buffer_size();

public:
  PyObject *_py_entity;
  PyObject *_dict;

  PredictionFields _fields;

  // Contains serialized prediction results for a number of
  // predicted command frames.
  PTA_uchar _data_slots[prediction_data_slots];
  PTA_uchar _original_data;

  int _intermediate_data_count;

  // The size of intermediate prediction result buffers.  This is the
  // total size of all fields.
  size_t _buffer_size;
};

#include "prediction.I"

#endif // PREDICTION_H

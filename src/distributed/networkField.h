/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkField.h
 * @author brian
 * @date 2022-05-03
 */

#ifndef NETWORKFIELD_H
#define NETWORKFIELD_H

#include "tfbase.h"
#include "namable.h"
#include <string>
#include "pnotify.h"
#include "datagram.h"
#include "datagramIterator.h"

class NetworkClass;

/**
 * Defines a single serializable field of a DataClass.
 */
class EXPCL_TF_DISTRIBUTED NetworkField : public Namable {
public:
  typedef const void *SerializeFunc(Datagram &dg, const unsigned char *data, const NetworkField *field);
  typedef void *UnserializeFunc(DatagramIterator &scan, unsigned char *data, const NetworkField *field);

  // The serialized data type.
  enum DataType {
    DT_unspecified, // Indicates that the serialized data type should be set
                    // to match the unserialized data type.
    DT_int8,
    DT_uint8,
    DT_int16,
    DT_uint16,
    DT_int32,
    DT_uint32,
    DT_int64,
    DT_uint64,
    DT_float32,
    DT_float64,
    DT_string,
    DT_blob, // An arbitrary sequence of bytes that are packed and unpacked
             // manually by the user.  Requires serialize and unserialize
             // functions.
    DT_class, // Reference to another DataClass.  Serializing the field
              // serializes the entire referenced DataClass.
  };

  // The unserialized in-memory data type.  The data type of the actual
  // member on the associated C++ class.
  enum NativeDataType {
    NDT_unspecified,
    NDT_int, // int32 / int
    NDT_uint, // uint32 / unsigned int
    NDT_float, // float32 / float
    NDT_double, // float64 / double
    NDT_bool,
    NDT_string,
    // Convenience types for linmath vectors.
    // Treats native type as LVecBase2/3/4f.  Reads/writes 2/3/4
    // DataTypes.
    NDT_vec2,
    NDT_vec3,
    NDT_vec4,
  };

  NetworkField(const std::string &name, size_t offset,
               NativeDataType native_type, DataType serialized_type = DT_unspecified,
               int array_size = 1, unsigned int divisor = 1, float modulus = 1.0f);
  NetworkField(const std::string &name, size_t offset,
               NetworkClass *cls, int array_size = 1);

  void serialize(Datagram &dg, const unsigned char *base) const;
  void unserialize(DatagramIterator &scan, unsigned char *base) const;

  template<class Type>
  INLINE void pack_numeric(Datagram &dg, Type value) const;
  INLINE void pack_string(Datagram &dg, const std::string &value) const;

  template<class Type>
  INLINE void unpack_numeric(DatagramIterator &scan, Type &value) const;
  INLINE void unpack_string(DatagramIterator &scan, std::string &value) const;

  INLINE uint16_t get_id() const;

  INLINE void set_serialize_func(SerializeFunc *func);
  INLINE SerializeFunc *get_serialize_func() const;

  INLINE void set_unserialize_func(UnserializeFunc *func);
  INLINE UnserializeFunc *get_unserialize_func() const;

  INLINE void set_divisor(unsigned int divisor);
  INLINE unsigned int get_divisor() const;

  size_t add_hash(size_t hash) const;

  void output(std::ostream &out, int indent_level) const;

private:
  DataType _data_type;
  NativeDataType _native_data_type;
  // 1 for non-arrays.
  uint32_t _array_size;
  // If field is another class, the pointer is stored here.
  NetworkClass *_class;
  size_t _offset;
  unsigned int _divisor;
  float _modulus;

  SerializeFunc *_serialize_func;
  UnserializeFunc *_unserialize_func;

  uint16_t _id;
};

#include "networkField.I"

#endif // NETWORKFIELD_H

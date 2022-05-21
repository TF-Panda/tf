/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkField.cxx
 * @author brian
 * @date 2022-05-03
 */

#include "networkField.h"
#include "datagram.h"
#include "cmath.h"
#include "networkClass.h"
#include "stl_compares.h"
#include "luse.h"
#include "indent.h"

/**
 *
 */
NetworkField::
NetworkField(const std::string &name, size_t offset,
             NativeDataType native_type, DataType serialized_type,
             int array_size, unsigned int divisor, float modulus) :
  Namable(name),
  _data_type(serialized_type),
  _native_data_type(native_type),
  _array_size(array_size),
  _class(nullptr),
  _offset(offset),
  _divisor(divisor),
  _modulus(modulus),
  _serialize_func(nullptr),
  _unserialize_func(nullptr),
  _id(0u)
{
}

/**
 *
 */
NetworkField::
NetworkField(const std::string &name, size_t offset,
             NetworkClass *cls, int array_size) :
  _data_type(DT_class),
  _native_data_type(NDT_unspecified),
  _array_size(array_size),
  _class(cls),
  _offset(offset),
  _divisor(1),
  _modulus(1.0f),
  _serialize_func(nullptr),
  _unserialize_func(nullptr),
  _id(0u)
{
}

/**
 * Adds the data for the field to the indicated datagram.
 */
void NetworkField::
serialize(Datagram &dg, const unsigned char *base) const {
  if (_serialize_func != nullptr) {
    (*_serialize_func)(dg, base, this);

  } else if (_class != nullptr) {
    for (int i = 0; i < _array_size; ++i) {
      _class->serialize(dg, base + _offset + _class->get_class_stride() * i);
    }

  } else {
    const unsigned char *data = base + _offset;
    for (int i = 0; i < _array_size; ++i) {
      switch (_native_data_type) {
      case NDT_int:
        {
          int value = *((int *)data + i);
          pack_numeric(dg, value);
        }
        break;
      case NDT_uint:
        {
          unsigned int value = *((unsigned int *)data + i);
          pack_numeric(dg, value);
        }
        break;
      case NDT_float:
        {
          float value = *((float *)data + i);
          pack_numeric(dg, value);
        }
        break;
      case NDT_double:
        {
          double value = *((double *)data + i);
          pack_numeric(dg, value);
        }
        break;
      case NDT_bool:
        {
          bool value = *((bool *)data + i);
          pack_numeric(dg, value);
        }
        break;
      case NDT_string:
        {
          const std::string &value = *((std::string *)data + i);
          pack_string(dg, value);
        }
        break;
      case NDT_vec2:
        {
          const LVecBase2f &value = *((LVecBase2f *)data + i);
          pack_numeric(dg, value[0]);
          pack_numeric(dg, value[1]);
        }
        break;
      case NDT_vec3:
        {
          const LVecBase3f &value = *((LVecBase3f *)data + i);
          pack_numeric(dg, value[0]);
          pack_numeric(dg, value[1]);
          pack_numeric(dg, value[2]);
        }
        break;
      case NDT_vec4:
        {
          const LVecBase4f &value = *((LVecBase4f *)data + i);
          pack_numeric(dg, value[0]);
          pack_numeric(dg, value[1]);
          pack_numeric(dg, value[2]);
          pack_numeric(dg, value[3]);
        }
        break;
      default:
        break;
      }
    }
  }
}

/**
 *
 */
void NetworkField::
unserialize(DatagramIterator &scan, unsigned char *base) const {
  if (_unserialize_func != nullptr) {
    (*_unserialize_func)(scan, base, this);

  } else if (_class != nullptr) {
    for (int i = 0; i < _array_size; ++i) {
      _class->unserialize(scan, base + _offset + _class->get_class_stride() * i);
    }

  } else {
    const unsigned char *data = base + _offset;
    for (int i = 0; i < _array_size; ++i) {
      switch (_native_data_type) {
      case NDT_int:
        unpack_numeric(scan, *((int *)data + i));
        break;
      case NDT_uint:
        unpack_numeric(scan, *((unsigned int *)data + i));
        break;
      case NDT_float:
        unpack_numeric(scan, *((float *)data + i));
        break;
      case NDT_double:
        unpack_numeric(scan, *((double *)data + i));
        break;
      case NDT_bool:
        unpack_numeric(scan, *((bool *)data + i));
        break;
      case NDT_string:
        unpack_string(scan, *((std::string *)data + i));
        break;
      case NDT_vec2:
        {
          LVecBase2f &value = *((LVecBase2f *)data + i);
          unpack_numeric(scan, value[0]);
          unpack_numeric(scan, value[1]);
        }
        break;
      case NDT_vec3:
        {
          LVecBase3f &value = *((LVecBase3f *)data + i);
          unpack_numeric(scan, value[0]);
          unpack_numeric(scan, value[1]);
          unpack_numeric(scan, value[2]);
        }
        break;
      case NDT_vec4:
        {
          LVecBase4f &value = *((LVecBase4f *)data + i);
          unpack_numeric(scan, value[0]);
          unpack_numeric(scan, value[1]);
          unpack_numeric(scan, value[2]);
          unpack_numeric(scan, value[3]);
        }
        break;
      default:
        break;
      }
    }
  }
}

/**
 *
 */
size_t NetworkField::
add_hash(size_t hash) const {
  hash = string_hash::add_hash(hash, get_name());
  hash = int_hash::add_hash(hash, _data_type);
  hash = int_hash::add_hash(hash, _native_data_type);
  hash = integer_hash<unsigned int>::add_hash(hash, _divisor);
  hash = float_hash().add_hash(hash, _modulus);
  hash = integer_hash<uint32_t>::add_hash(hash, _array_size);
  if (_class != nullptr) {
    hash = _class->add_hash(hash);
  }
  return hash;
}

/**
 *
 */
void NetworkField::
output(std::ostream &out, int indent_level) const {
  indent(out, indent_level) << "Field " << get_name() << "\n";
  indent(out, indent_level + 2) << "Serialized type: " << _data_type << "\n";
  indent(out, indent_level + 2) << "Native type: " << _native_data_type << "\n";
  indent(out, indent_level + 2) << "Offset: " << _offset << "\n";
  indent(out, indent_level + 2) << "Array size: " << _array_size << "\n";
  indent(out, indent_level + 2) << "Divisor: " << _divisor << "\n";
  indent(out, indent_level + 2) << "Modulus: " << _modulus << "\n";
  indent(out, indent_level + 2) << "Class ref: " << _class << "\n";
  indent(out, indent_level + 2) << "Serialize func: " << _serialize_func << "\n";
  indent(out, indent_level + 2) << "Unserialize func: " << _unserialize_func << "\n";
}

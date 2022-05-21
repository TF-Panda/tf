/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkField.I
 * @author brian
 * @date 2022-05-03
 */

/**
 *
 */
template<class Type>
INLINE void NetworkField::
pack_numeric(Datagram &dg, Type value) const {
  std::cout << "packing numeric " << value << "\n";
  value *= _divisor;
  switch (_data_type) {
  case DT_int8:
    dg.add_int8(value);
    break;
  case DT_uint8:
    dg.add_uint8(value);
    break;
  case DT_int16:
    dg.add_int16(value);
    break;
  case DT_uint16:
    dg.add_uint16(value);
    break;
  case DT_int32:
    dg.add_int32(value);
    break;
  case DT_uint32:
    dg.add_uint32(value);
    break;
  case DT_float32:
    dg.add_float32(value);
    break;
  case DT_float64:
    dg.add_float64(value);
    break;
  default:
    nassert_raise("pack_numeric() cannot pack value as a non-numeric data type");
    break;
  }
}

/**
 *
 */
INLINE void NetworkField::
pack_string(Datagram &dg, const std::string &value) const {
  nassertv(_data_type == DT_string);
  dg.add_string(value);
}


/**
 *
 */
template<class Type>
INLINE void NetworkField::
unpack_numeric(DatagramIterator &scan, Type &value) const {
  switch (_data_type) {
  case DT_int8:
    value = scan.get_int8();
    break;
  case DT_uint8:
    value = scan.get_uint8();
    break;
  case DT_int16:
    value = scan.get_int16();
    break;
  case DT_uint16:
    value = scan.get_uint16();
    break;
  case DT_int32:
    value = scan.get_int32();
    break;
  case DT_uint32:
    value = scan.get_uint32();
    break;
  case DT_int64:
    value = scan.get_int64();
    break;
  case DT_uint64:
    value = scan.get_uint64();
    break;
  case DT_float32:
    value = scan.get_float32();
    break;
  case DT_float64:
    value = scan.get_float64();
    break;
  default:
    break;
  }
  value /= _divisor;
  std::cout << "unpacked numeric " << value << "\n";
}

/**
 *
 */
INLINE void NetworkField::
unpack_string(DatagramIterator &scan, std::string &value) const {
  nassertv(_data_type == DT_string);
  value = scan.get_string();
}

/**
 *
 */
INLINE uint16_t NetworkField::
get_id() const {
  return _id;
}

/**
 *
 */
INLINE void NetworkField::
set_serialize_func(SerializeFunc *func) {
  _serialize_func = func;
}

/**
 *
 */
INLINE NetworkField::SerializeFunc *NetworkField::
get_serialize_func() const {
  return _serialize_func;
}

/**
 *
 */
INLINE void NetworkField::
set_unserialize_func(UnserializeFunc *func) {
  _unserialize_func = func;
}

/**
 *
 */
INLINE NetworkField::UnserializeFunc *NetworkField::
get_unserialize_func() const {
  return _unserialize_func;
}

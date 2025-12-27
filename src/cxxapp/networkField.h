#ifndef NETWORKFIELD_H
#define NETWORKFIELD_H

#include "pandabase.h"
#include "datagramIterator.h"
#include "datagram.h"

class NetworkClass;

/**
 * Describes a field on a networked class that is to be serialized from a data source and
 * deserialized on another end and stored.
 *
 * For most basic types, like ints, floats, etc, the field is capable of automatically
 * reading the data source off of the entity and encoding the data.  Fixed length vectors of
 * all these types are also supported.
 *
 * The field contains two different data types, one for the source/destination memory on the
 * entity itself, and another for the actual encoding that is stored/sent over the network.
 * These may be different to optimize network bandwidth.
 *
 * For integer types, the field may provide a fixed point divisor for encoding.  This is
 * to encode floating point fields into fixed point float to reduce network bandwidth.
 */
struct NetworkField {
  enum DataType {
    DT_float,

    DT_bool,

    DT_int8,
    DT_char,
    DT_uint8,
    DT_uchar,

    DT_int16,
    DT_short,
    DT_uint16,
    DT_ushort,

    DT_int,
    DT_int32,
    DT_uint,
    DT_uint32,

    DT_int64,
    DT_uint64,

    DT_string,

    // Nested NetworkClass/structure.
    DT_class,
  };

  typedef void (*IndirectFetchFunc)(void *object, void *dest);
  typedef void (*IndirectWriteFunc)(void *object, void *data);
  typedef void *(*IndirectFetchPtrFunc)(void *object);
  typedef void *(*IndirectWritePtrFunc)(void *object);

  std::string name = "";

  // What is the data type of the source/destination memory on the entity?
  DataType source_type = NetworkField::DT_char;

  // What is the data type of the encoded data for the field?
  DataType encoding_type = NetworkField::DT_char;

  // What is the byte offset into the entity's memory block where the
  // source/destination memory resides?
  size_t offset = 0u;

  // To read array memory correctly, exactly how big is one element.
  size_t stride = 0u;

  // For arrays, how big is it?
  size_t count = 1u;

  // For float encoding.
  int divisor = 1;
  float modulo = 0.0f;

  const NetworkClass *net_class = nullptr;

  size_t id = 0u;

  IndirectFetchFunc indirect_fetch = nullptr;
  IndirectFetchPtrFunc indirect_fetch_ptr = nullptr;
  IndirectWriteFunc indirect_write = nullptr;
  IndirectWritePtrFunc indirect_write_ptr = nullptr;

  void write(void *object, Datagram &dg) const;
  void read(void *object, DatagramIterator &scan) const;

  void output(std::ostream &out, int indent_level = 0) const;
};

template<typename T>
struct NetworkFieldTypeTraits {
  static_assert(false, "Unsupported network field type");
};

template<>
struct NetworkFieldTypeTraits<float> {
  static constexpr NetworkField::DataType type = NetworkField::DT_float;
  static constexpr size_t count = 1u;
  static constexpr size_t stride = sizeof(float);
};

template<>
struct NetworkFieldTypeTraits<int> {
  static constexpr NetworkField::DataType type = NetworkField::DT_int32;
  static constexpr size_t count = 1u;
  static constexpr size_t stride = sizeof(int);
};

template<>
struct NetworkFieldTypeTraits<unsigned int> {
  static constexpr NetworkField::DataType type = NetworkField::DT_uint32;
  static constexpr size_t count = 1u;
  static constexpr size_t stride = sizeof(unsigned int);
};

template<>
struct NetworkFieldTypeTraits<std::string> {
  static constexpr NetworkField::DataType type = NetworkField::DT_string;
  static constexpr size_t count = 1u;
  static constexpr size_t stride = sizeof(std::string);
};

template<>
struct NetworkFieldTypeTraits<bool> {
  static constexpr NetworkField::DataType type = NetworkField::DT_bool;
  static constexpr size_t count = 1u;
  static constexpr size_t stride = sizeof(bool);
};

template<typename T, size_t N>
struct NetworkFieldTypeTraits<std::array<T, N>> {
  static constexpr NetworkField::DataType type =
      NetworkFieldTypeTraits<T>::type;
  static constexpr size_t count = N;
  static constexpr size_t stride = NetworkFieldTypeTraits<T>::stride;
};

template<typename T, size_t N>
struct NetworkFieldTypeTraits<T[N]> {
  static constexpr NetworkField::DataType type =
      NetworkFieldTypeTraits<T>::type;
  static constexpr size_t count = N;
  static constexpr size_t stride = NetworkFieldTypeTraits<T>::stride;
};

#endif // NETWORKFIELD_H

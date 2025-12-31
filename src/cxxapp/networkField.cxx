#include "networkField.h"
#include <cmath>
#include "networkClass.h"
#include "indent.h"
#include <limits>

/**
 *
 */
std::string
network_field_type_string(NetworkField::DataType type) {
  switch (type) {
  case NetworkField::DT_uchar:
  case NetworkField::DT_uint8:
    return "uint8";
  case NetworkField::DT_char:
  case NetworkField::DT_int8:
    return "int8";
  case NetworkField::DT_bool:
    return "bool";
  case NetworkField::DT_int16:
  case NetworkField::DT_short:
    return "int16";
  case NetworkField::DT_uint16:
  case NetworkField::DT_ushort:
    return "uint16";
  case NetworkField::DT_int32:
  case NetworkField::DT_int:
    return "int32";
  case NetworkField::DT_uint32:
  case NetworkField::DT_uint:
    return "uint32";
  case NetworkField::DT_int64:
    return "int64";
  case NetworkField::DT_uint64:
    return "uint64";
  case NetworkField::DT_string:
    return "string";
  case NetworkField::DT_float:
    return "float32";
  case NetworkField::DT_class:
    return "class";
  case NetworkField::DT_datagram:
    return "datagram";
  default:
    return "";
  }
}

/**
 *
 */
void
write_dg(Datagram &dg, int8_t data) {
  dg.add_int8(data);
}

void
write_dg(Datagram &dg, uint8_t data) {
  dg.add_uint8(data);
}

void
write_dg(Datagram &dg, int16_t data) {
  dg.add_int16(data);
}

/**
 *
 */
void
write_dg(Datagram &dg, uint16_t data) {
  dg.add_uint16(data);
}

void
write_dg(Datagram &dg, float data) {
  dg.add_float32(data);
}

void
write_dg(Datagram &dg, bool data) {
  dg.add_bool(data);
}

void
write_dg(Datagram &dg, int32_t data) {
  dg.add_int32(data);
}

void
write_dg(Datagram &dg, uint32_t data) {
  dg.add_uint32(data);
}

void
write_dg(Datagram &dg, int64_t data) {
  dg.add_int64(data);
}

void
write_dg(Datagram &dg, uint64_t data) {
  dg.add_uint64(data);
}

void
write_dg(Datagram &dg, const std::string &data) {
  dg.add_string(data);
}

/**
 * Converts float_val into fixed point integer of a specific int type.
 * Divisor is the number of decimal places.
 */
template<typename T>
T
fixed_point_encode(float float_val, int divisor) {
  T val = (T)(float_val * divisor);
  return val;
}

/**
 * Generic writer for integer source types.  Basic casts with
 * truncation/expansion.
 */
template<typename T>
void
generic_int_write(Datagram &dg, NetworkField::DataType encoding_type,
                  unsigned char *&data_ptr) {
  T source_val = *(T *)data_ptr;
  switch (encoding_type) {
  case NetworkField::DT_int8:
  case NetworkField::DT_char:
    write_dg(dg, (int8_t)source_val);
    break;
  case NetworkField::DT_uint8:
  case NetworkField::DT_uchar:
    write_dg(dg, (uint8_t)source_val);
    break;
  case NetworkField::DT_int16:
  case NetworkField::DT_short:
    write_dg(dg, (int16_t)source_val);
    break;
  case NetworkField::DT_uint16:
  case NetworkField::DT_ushort:
    write_dg(dg, (uint16_t)source_val);
    break;
  case NetworkField::DT_int:
  case NetworkField::DT_int32:
    write_dg(dg, (int32_t)source_val);
    break;
  case NetworkField::DT_uint:
  case NetworkField::DT_uint32:
    write_dg(dg, (uint32_t)source_val);
    break;
  case NetworkField::DT_int64:
    write_dg(dg, (int64_t)source_val);
    break;
  case NetworkField::DT_uint64:
    write_dg(dg, (uint64_t)source_val);
    break;
  case NetworkField::DT_float:
    write_dg(dg, (float)source_val);
    break;
  case NetworkField::DT_bool:
    write_dg(dg, (bool)(source_val != 0));
    break;
  default:
    nassert_raise("Cannot write integer to " + network_field_type_string(encoding_type));
    break;
  }
}

/**
 *
 */
template<typename T>
void
generic_int_read(DatagramIterator &scan, NetworkField::DataType encoding_type,
                 unsigned char *data_ptr) {
  T dest_val = 0;

  switch (encoding_type) {
  case NetworkField::DT_int8:
  case NetworkField::DT_char:
    dest_val = scan.get_int8();
    break;
  case NetworkField::DT_uint8:
  case NetworkField::DT_uchar:
    dest_val = scan.get_uint8();
    break;
  case NetworkField::DT_int16:
  case NetworkField::DT_short:
    dest_val = scan.get_int16();
    break;
  case NetworkField::DT_uint16:
  case NetworkField::DT_ushort:
    dest_val = scan.get_uint16();
    break;
  case NetworkField::DT_int32:
  case NetworkField::DT_int:
    dest_val = scan.get_int32();
    break;
  case NetworkField::DT_uint32:
  case NetworkField::DT_uint:
    dest_val = scan.get_uint32();
    break;
  case NetworkField::DT_int64:
    dest_val = scan.get_int64();
    break;
  case NetworkField::DT_uint64:
    dest_val = scan.get_uint64();
    break;
  case NetworkField::DT_float:
    dest_val = (T)scan.get_float32();
    break;
  case NetworkField::DT_bool:
    dest_val = (T)scan.get_bool();
    break;
  default:
    nassert_raise("Cannot read " + network_field_type_string(encoding_type) + " to integer");
    break;
  }

  *(T *)data_ptr = dest_val;
}

/**
 * Writer for a float source type.  If encoding type is an integer, performs
 * fixed point conversion.
 */
void
float_write(Datagram &dg, int divisor, float modulo, NetworkField::DataType encoding_type,
            unsigned char *&data_ptr) {
  float float_val = *(float *)data_ptr;
  if (modulo != 0.0f) {
    float_val = fmodf(float_val, modulo);
  }
  switch (encoding_type) {
  case NetworkField::DT_float:
    // Easy passthrough.
    write_dg(dg, float_val);
    break;
  case NetworkField::DT_int8:
  case NetworkField::DT_char:
    write_dg(dg, fixed_point_encode<int8_t>(float_val, divisor));
    break;
  case NetworkField::DT_uint8:
  case NetworkField::DT_uchar:
    write_dg(dg, fixed_point_encode<uint8_t>(float_val, divisor));
    break;
  case NetworkField::DT_int16:
  case NetworkField::DT_short:
    write_dg(dg, fixed_point_encode<int16_t>(float_val, divisor));
    break;
  case NetworkField::DT_uint16:
  case NetworkField::DT_ushort:
    write_dg(dg, fixed_point_encode<uint16_t>(float_val, divisor));
    break;
  case NetworkField::DT_int:
  case NetworkField::DT_int32:
    write_dg(dg, fixed_point_encode<int32_t>(float_val, divisor));
    break;
  case NetworkField::DT_uint:
  case NetworkField::DT_uint32:
    write_dg(dg, fixed_point_encode<uint32_t>(float_val, divisor));
    break;
  case NetworkField::DT_int64:
    write_dg(dg, fixed_point_encode<int64_t>(float_val, divisor));
    break;
  case NetworkField::DT_uint64:
    write_dg(dg, fixed_point_encode<uint64_t>(float_val, divisor));
    break;
  default:
    nassert_raise("Cannot write float to " + network_field_type_string(encoding_type));
    break;
  }
}

/**
 *
 */
static void
float_read(unsigned char *data_ptr, int divisor,
           NetworkField::DataType encoding_type, DatagramIterator &scan) {
  float float_val = 0.0f;

  switch (encoding_type) {
  case NetworkField::DT_float:
    float_val = scan.get_float32();
    break;
  case NetworkField::DT_int8:
  case NetworkField::DT_char:
    float_val = (float)scan.get_int8() / divisor;
    break;
  case NetworkField::DT_uint8:
  case NetworkField::DT_uchar:
    float_val = (float)scan.get_uint8() / divisor;
    break;
  case NetworkField::DT_int16:
  case NetworkField::DT_short:
    float_val = (float)scan.get_int16() / divisor;
    break;
  case NetworkField::DT_uint16:
  case NetworkField::DT_ushort:
    float_val = (float)scan.get_uint16() / divisor;
    break;
  case NetworkField::DT_int32:
  case NetworkField::DT_int:
    float_val = (float)scan.get_int32() / divisor;
    break;
  case NetworkField::DT_uint32:
  case NetworkField::DT_uint:
    float_val = (float)scan.get_uint32() / divisor;
    break;
  case NetworkField::DT_int64:
    float_val = (float)scan.get_int64() / divisor;
    break;
  case NetworkField::DT_uint64:
    float_val = (float)scan.get_uint64() / divisor;
    break;
  case NetworkField::DT_bool:
    float_val = scan.get_bool() ? 1.0f : 0.0f;
    break;
  default:
    nassert_raise("Cannot read " + network_field_type_string(encoding_type) + " to float");
    break;
  }

  *(float *)data_ptr = float_val;
}

/**
 * Encodes the field into the datagram for the given object/entity.
 */
void
NetworkField::write(void *object, Datagram &dg) const {
  unsigned char *data_ptr;

  constexpr int stack_buffer_size = 256;
  char stack_buffer[stack_buffer_size];

  if (indirect_fetch != nullptr) {
    // The field provides us with a function to copy the field memory
    // from somewhere into a local scratch buffer for us.

    void *scratch_ptr;
    assert((stride * count + (alignment - 1)) <= stack_buffer_size);
    scratch_ptr = align_ptr(stack_buffer, alignment);

    data_ptr = (unsigned char *)scratch_ptr;
    if (source_type == DT_string || source_type == DT_datagram) {
      for (int i = 0; i < count; ++i) {
	if (source_type == DT_string) {
	  new(data_ptr) std::string();
	} else {
	  new(data_ptr) Datagram();
	}
	data_ptr += stride;
      }
    }
    (*indirect_fetch)(object, scratch_ptr);
    data_ptr = (unsigned char *)scratch_ptr;

  } else if (indirect_fetch_ptr != nullptr) {
    // The field provides us with a function to retrieve the data pointer
    // for the field.
    data_ptr = (unsigned char *)(*indirect_fetch_ptr)(object);

  } else {
    // Use raw offset into entity memory block.
    data_ptr = (unsigned char *)object + offset;
  }

  unsigned char *start_data_ptr = data_ptr;

  for (int i = 0; i < count; ++i) {
    assert(((uintptr_t)data_ptr & (alignment - 1)) == 0);
    switch (source_type) {
    case DT_float:
      float_write(dg, divisor, modulo, encoding_type, data_ptr);
      break;

    case DT_int8:
    case DT_char:
      generic_int_write<int8_t>(dg, encoding_type, data_ptr);
      break;

    case DT_uint8:
    case DT_uchar:
      generic_int_write<uint8_t>(dg, encoding_type, data_ptr);
      break;

    case DT_int16:
    case DT_short:
      generic_int_write<int16_t>(dg, encoding_type, data_ptr);
      break;

    case DT_uint16:
    case DT_ushort:
      generic_int_write<uint16_t>(dg, encoding_type, data_ptr);
      break;

    case DT_int:
    case DT_int32:
      generic_int_write<int32_t>(dg, encoding_type, data_ptr);
      break;

    case DT_uint:
    case DT_uint32:
      generic_int_write<uint32_t>(dg, encoding_type, data_ptr);
      break;

    case DT_int64:
      generic_int_write<int64_t>(dg, encoding_type, data_ptr);
      break;

    case DT_uint64:
      generic_int_write<uint64_t>(dg, encoding_type, data_ptr);
      break;

    case DT_string:
      {
	//std::string val = *(std::string *)data_ptr;
	write_dg(dg, *(std::string *)data_ptr);
      }
      break;

    case DT_datagram:
      {
	Datagram *field_dg = (Datagram *)data_ptr;
	size_t field_len = field_dg->get_length();
	assert(field_len <= std::numeric_limits<uint16_t>::max());
	dg.add_uint16(field_len);
	dg.append_data(field_dg->get_data(), field_len);
      }
      break;

    case DT_class:
      net_class->write(data_ptr, dg);
      break;

    default:
      nassert_raise("Don't know how to write source type " + network_field_type_string(source_type));
      break;
    }

    data_ptr += stride;
  }

  if (indirect_fetch != nullptr) {
    // Destruct strings.
    using string_type = std::string;
    if (source_type == DT_string || source_type == DT_datagram) {
      data_ptr = start_data_ptr;
      for (int i = 0; i < count; ++i) {
	if (source_type == DT_string) {
	  ((string_type *)data_ptr)->~string_type();
	} else {
	  ((Datagram *)data_ptr)->~Datagram();
	}
	data_ptr += stride;
      }
    }
  }
}

/**
 *
 */
void
NetworkField::read(void *object, DatagramIterator &scan) const {
  unsigned char *data_ptr;
  unsigned char *start_data_ptr;

  constexpr int stack_buffer_size = 256;
  char stack_buffer[stack_buffer_size];

  if (indirect_write_ptr != nullptr) {
    // Pointer to deserialize to is provided from this function.
    data_ptr = (unsigned char *)(*indirect_write_ptr)(object);

  } else if (indirect_write != nullptr) {
    // We will deserialize the field into a temporary structure that
    // will be copied into object memory by the indirect write function.

    void *scratch_ptr;
    assert((stride * count + (alignment - 1)) <= stack_buffer_size);
    scratch_ptr = align_ptr(stack_buffer, alignment);

    data_ptr = (unsigned char *)scratch_ptr;
    start_data_ptr = data_ptr;
    if (source_type == DT_string || source_type == DT_datagram) {
      // We need to construct strings.
      for (int i = 0; i < count; ++i) {
	if (source_type == DT_string) {
	  new(data_ptr) std::string();
	} else {
	  new(data_ptr) Datagram();
	}
	data_ptr += stride;
      }
      data_ptr = start_data_ptr;
    }

  } else {
    // We have a fixed offset from the start of the object of where
    // to deserialize the field to.
    data_ptr = (unsigned char *)object + offset;
  }

  start_data_ptr = data_ptr;

  for (int i = 0; i < count; ++i) {
    assert(((uintptr_t)data_ptr & (alignment - 1)) == 0);
    switch (source_type) {
    case DT_float:
      float_read(data_ptr, divisor, encoding_type, scan);
      break;
    case DT_int8:
    case DT_char:
      generic_int_read<int8_t>(scan, encoding_type, data_ptr);
      break;
    case DT_uint8:
    case DT_uchar:
      generic_int_read<uint8_t>(scan, encoding_type, data_ptr);
      break;
    case DT_int16:
    case DT_short:
      generic_int_read<int16_t>(scan, encoding_type, data_ptr);
      break;
    case DT_uint16:
    case DT_ushort:
      generic_int_read<uint16_t>(scan, encoding_type, data_ptr);
      break;
    case DT_int32:
    case DT_int:
      generic_int_read<int32_t>(scan, encoding_type, data_ptr);
      break;
    case DT_uint32:
    case DT_uint:
      generic_int_read<uint32_t>(scan, encoding_type, data_ptr);
      break;
    case DT_int64:
      generic_int_read<int64_t>(scan, encoding_type, data_ptr);
      break;
    case DT_uint64:
      generic_int_read<uint64_t>(scan, encoding_type, data_ptr);
      break;
    case DT_string:
      *(std::string *)data_ptr = scan.get_string();
      break;
    case DT_bool:
      *(bool *)data_ptr = scan.get_bool();
      break;
    case DT_class:
      net_class->read(data_ptr, scan);
      break;
    case DT_datagram:
      {
	Datagram *field_dg = (Datagram *)data_ptr;
	uint16_t len = scan.get_uint16();
	unsigned char *blob_data = (unsigned char *)scan.get_datagram().get_data() + scan.get_current_index();
	field_dg->assign(blob_data, len);
	scan.skip_bytes(len);
      }
      break;
    default:
      nassert_raise("Don't know how to read into source type " + network_field_type_string(source_type));
      break;
    }
    data_ptr += stride;
  }

  if (indirect_write != nullptr) {
    // Pass our deserialized temp object into the write function.
    // Function should copy to real object memory.
    (*indirect_write)(object, start_data_ptr);

    // Destruct strings.
    if (source_type == DT_string || source_type == DT_datagram) {
      using string_type = std::string;
      data_ptr = start_data_ptr;
      for (int i = 0; i < count; ++i) {
	if (source_type == DT_string) {
	  ((string_type *)data_ptr)->~string_type();
	} else {
	  ((Datagram *)data_ptr)->~Datagram();
	}
	data_ptr += stride;
      }
    }
  }
}

/**
 *
 */
void
NetworkField::output(std::ostream &out, int indent_level) const {
  indent(out, indent_level) << "field " << name << "\n";
  if (indirect_fetch != nullptr || indirect_write != nullptr) {
    indent(out, indent_level + 2)
        << "indirect read/write, don't know exact memory location\n";
  } else {
    indent(out, indent_level + 2) << "offset " << offset << " bytes\n";
  }
  if (net_class != nullptr) {
    net_class->output(out, indent_level + 2);
  } else {
    indent(out, indent_level + 2)
        << "in memory as " << network_field_type_string(source_type) << "["
        << count << "], stride " << stride << " bytes\n";
    indent(out, indent_level + 2)
      << "encode as " << network_field_type_string(encoding_type) << "\n";
  }
}

#include "networkClass.h"
#include "luse.h"

NetworkClassRegistry *NetworkClassRegistry::_ptr = nullptr;

void write_dg(Datagram &dg, int8_t data) {
  dg.add_int8(data);
}

void write_dg(Datagram &dg, uint8_t data) {
  dg.add_uint8(data);
}

void write_dg(Datagram &dg, int16_t data) {
  dg.add_int16(data);
}

void write_dg(Datagram &dg, uint16_t data) {
  dg.add_uint16(data);
}

void write_dg(Datagram &dg, float data) {
  dg.add_float32(data);
}

void write_dg(Datagram &dg, bool data) {
  dg.add_bool(data);
}

void write_dg(Datagram &dg, int32_t data) {
  dg.add_int32(data);
}

void write_dg(Datagram &dg, uint32_t data) {
  dg.add_uint32(data);
}

void write_dg(Datagram &dg, int64_t data) {
  dg.add_int64(data);
}

void write_dg(Datagram &dg, uint64_t data) {
  dg.add_uint64(data);
}

void write_dg(Datagram &dg, const std::string &data) {
  dg.add_string(data);
}

void write_dg(Datagram &dg, const LVecBase3f &data) {
  data.write_datagram_fixed(dg);
}

void write_dg(Datagram &dg, const LVecBase2f &data) {
  data.write_datagram_fixed(dg);
}

void write_dg(Datagram &dg, const LVecBase4f &data) {
  data.write_datagram_fixed(dg);
}

template<typename T>
T fixed_point_encode(float float_val, int divisor) {
  T val = (T)(float_val * divisor);
  return val;
}

/**
 * Generic writer for integer source types.  Basic casts with truncation/expansion.
 */
template<typename T>
void generic_int_write(Datagram &dg, NetworkField::DataType encoding_type, unsigned char *&data_ptr) {
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
    break;
  }
}

template<typename T>
void generic_int_read(DatagramIterator &scan, NetworkField::DataType encoding_type, unsigned char *data_ptr) {
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
    nassertv(false);
    break;
  }

  *(T *)data_ptr = dest_val;
}

/**
 * Writer for a float source type.  If encoding type is an integer, performs fixed point conversion.
 */
void float_write(Datagram &dg, float divisor, NetworkField::DataType encoding_type, unsigned char *&data_ptr) {
  float float_val = *(float *)data_ptr;
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
    break;
  }
}

static void float_read(unsigned char *data_ptr, int divisor, NetworkField::DataType encoding_type, DatagramIterator &scan) {
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
    nassertv(false);
    break;
  }

  *(float *)data_ptr = float_val;
}

/**
 * Encodes the field into the datagram for the given object/entity.
 */
void NetworkField::
write(void *object, Datagram &dg) const {
  unsigned char *data_ptr;

  if (indirect_fetch != nullptr) {
    // The field provides us with a function to copy the field memory
    // from somewhere into a local scratch buffer for us.
    void *scratch_ptr = alloca(stride * count);
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

  for (int i = 0; i < count; ++i) {
    switch (source_type) {
    case DT_float:
      float_write(dg, divisor, encoding_type, data_ptr);
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
      write_dg(dg, *(std::string *)data_ptr);
      break;

    case DT_class:
      net_class->write(data_ptr, dg);
      break;

    default:
      nassertv(false);
      break;
    }

    data_ptr += stride;
  }
}

void NetworkField::
read(void *object, DatagramIterator &scan) const {
  unsigned char *data_ptr;
  unsigned char *start_data_ptr;

  if (indirect_write_ptr != nullptr) {
    // Pointer to deserialize to is provided from this function.
    data_ptr = (unsigned char *)(*indirect_write_ptr)(object);

  } else if (indirect_write != nullptr) {
    // We will deserialize the field into a temporary structure that
    // will be copied into object memory by the indirect write function.
    data_ptr = (unsigned char *)alloca(stride * count);

  } else {
    // We have a fixed offset from the start of the object of where
    // to deserialize the field to.
    data_ptr = (unsigned char *)object + offset;
  }

  start_data_ptr = data_ptr;

  for (int i = 0; i < count; ++i) {
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
    default:
      nassertv(false);
      break;
    }
    data_ptr += stride;
  }

  if (indirect_write != nullptr) {
    // Pass our deserialized temp object into the write function.
    // Function should copy to real object memory.
    (*indirect_write)(object, start_data_ptr);
  }
}

/**
 * Encodes all fields of this class into the datagram, including nested class fields.
 */
void NetworkClass::
write(void *object, Datagram &dg) const {
  for (size_t i = 0; i < _inherited_fields.size(); ++i) {
    NetworkField *field = _inherited_fields[i];
    field->write(object, dg);
  }
}

/**
 * Reads all fields from the datagram and stores them on the provided object.
 */
void NetworkClass::
read(void *object, DatagramIterator &scan) const {
  for (size_t i = 0; i < _inherited_fields.size(); ++i) {
    NetworkField *field = _inherited_fields[i];
    field->read(object, scan);
  }
}

/**
 *
 */
void NetworkClass::
inherit_fields() {
  if (_built_inherited_fields) {
    return;
  }

  if (_parent != nullptr) {
    // Inherit fields from parent.
    // Make sure they've inherited their own fields too.
    _parent->inherit_fields();
    _inherited_fields.insert(_inherited_fields.end(), _parent->_inherited_fields.begin(), _parent->_inherited_fields.end());
  }

  // Add our own fields.
  _inherited_fields.insert(_inherited_fields.end(), _fields.begin(), _fields.end());

  // Sort fields by name.
  std::sort(_inherited_fields.begin(), _inherited_fields.end(), [](NetworkField *a, NetworkField *b)
  {
    return a->name < b->name;
  });

  _built_inherited_fields = true;
}

void NetworkClassRegistry::
register_class(NetworkClass *cls) {
  // Inherit fields from parent onto child class if it has a parent.
  cls->inherit_fields();

  _classes.push_back(cls);
  _classes_by_name.insert({ cls->get_name(), cls });
}

void NetworkClassRegistry::
build_ids() {
  // Order all classes by name.  Assign IDs in order.

  size_t current_id = 1u;
  std::sort(_classes.begin(), _classes.end(), [](NetworkClass *a, NetworkClass *b)
  {
    return a->get_name() < b->get_name();
  });

  pvector<NetworkField *> all_fields;
  pvector<NetworkField *> local_fields;

  for (size_t i = 0; i < _classes.size(); ++i) {
    local_fields.clear();

    _classes[i]->set_id(current_id++);
    _classes_by_id.insert({ _classes[i]->get_id(), _classes[i] });

    for (size_t j = 0; j < _classes[i]->get_num_fields(); ++j) {
      local_fields.push_back(_classes[i]->get_field(j));
    }

    // Sort local fields within class (not including inherited ones), then add to global field list.
    std::sort(local_fields.begin(), local_fields.end(), [](NetworkField *a, NetworkField *b)
    {
      return a->name < b->name;
    });

    all_fields.insert(all_fields.end(), local_fields.begin(), local_fields.end());
  }

  current_id = 1u;
  // Now assign field IDs.
  for (size_t i = 0; i < all_fields.size(); ++i) {
    all_fields[i]->id = current_id++;
  }
}

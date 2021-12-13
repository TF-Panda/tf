/**
 * Proof-of-concept program for DC files with C++ classes and the RTTR library.
 *
 * @file test_dc_rttr.cxx
 * @author brian
 * @date 2021-11-11
 */

#include "dcFile.h"
#include "dcClass.h"
#include "dcPacker.h"
#include "typedObject.h"
#include "pmap.h"
#include "pvector.h"
#include "luse.h"

class FieldData {
public:
  enum FieldType {
    FT_none,
    FT_int,
    FT_uint,
    FT_float,
    FT_double,
    FT_int64,
    FT_uint64,
    FT_string,
    // We make special cases for linmath types, which are very common.
    FT_vec2f,
    FT_vec3f,
    FT_vec4f,
    FT_vec2d,
    FT_vec3d,
    FT_vec4d,
    // Otherwise, if a custom structure is needed, register its
    // class and data fields and link it up to the field.
    FT_class,
  };

  FieldType _type;
  std::string _name;
  size_t _offset;
  size_t _size;

  // The field might be another class.
  ClassData *_class;

  /**
   * Returns the number of bytes taken up by a single
   * data element of the field.  Divide this by _size
   * to get the number of array elements.
   */
  INLINE size_t get_element_size() const {
    switch (_type) {
      case FT_none:
        return 0;
      case FT_int:
      case FT_uint:
      case FT_float:
        return 4;
      case FT_double:
      case FT_int64:
      case FT_uint64:
        return 8;
      case FT_string:
        return sizeof(std::string);
      case FT_class:
        return _class->get_class_size();
      case FT_vec2f:
        return sizeof(float) * 2;
      case FT_vec3f:
        return sizeof(float) * 3;
      case FT_vec4f:
        return sizeof(float) * 4;
      case FT_vec2d:
        return sizeof(double) * 2;
      case FT_vec3d:
        return sizeof(double) * 3;
      case FT_vec4d:
        return sizeof(double) * 4;
    }
  }

  /**
   * Returns the number of array elements in the field.
   * Divides the variable size by the size of one element.
   */
  INLINE size_t get_num_elements() const {
    size_t elem_size = get_element_size();
    if (elem_size == 0) {
      return 0;
    }
    return _size / elem_size;
  }
};

class ClassData {
public:
  std::string _name;
  typedef pvector<FieldData> Fields;
  Fields _fields;

  /**
   * Returns the number of bytes taken up by all fields of the class,
   * including parent class fields.
   */
  INLINE size_t get_class_size() const {
    size_t size = 0;
    for (size_t i = 0; i < _fields.size(); i++) {
      size += _fields[i].get_element_size() * _fields[i].get_num_elements();
    }
  };
};

class TestObject {
public:
  int _foo;
  float _bar;
  std::string _name;

  static ClassData *_class_data;
};

ClassData *TestObject::_class_data = nullptr;

int
main(int argc, char *argv[]) {

  TestObject::_class_data = new ClassData;
  FieldData foo_data;
  foo_data._name = "_foo";
  foo_data._type = FieldData::FT_int;
  foo_data._offset = offsetof(TestObject, _foo);
  foo_data._size = sizeof(TestObject::_foo);
  FieldData bar_data;
  bar_data._name = "_bar";
  bar_data._type = FieldData::FT_float;
  bar_data._offset = offsetof(TestObject, _bar);
  bar_data._size = sizeof(TestObject::_bar);
  FieldData name_data;
  name_data._name = "_name";
  name_data._type = FieldData::FT_string;
  name_data._offset = offsetof(TestObject, _name);
  name_data._size = sizeof(TestObject::_name);
  TestObject::_class_data->_fields.push_back(foo_data);
  TestObject::_class_data->_fields.push_back(bar_data);
  TestObject::_class_data->_fields.push_back(name_data);

  DCFile dc;
  dc.read("/c/Users/brian/player/test_cxx.dc");

  TestObject my_test_obj;
  my_test_obj._foo = 3;
  my_test_obj._bar = 5.97f;
  my_test_obj._name = "brian";

  TestObject recv_obj;

  DCClass *dclass = dc.get_class_by_name("TestObject");
  ClassData *cls_data = TestObject::_class_data;
  unsigned char *object = (unsigned char *)&my_test_obj;

  DCPacker packer;
  for (int i = 0; i < dclass->get_num_inherited_fields(); i++) {
    DCField *field = dclass->get_inherited_field(i);

    packer.begin_pack(field);

    int field_idx = -1;
    for (int j = 0; j < cls_data->_fields.size(); j++) {
      if (cls_data->_fields[j]._name == field->get_name()) {
        field_idx = j;
        break;
      }
    }

    if (field_idx == -1) {
      packer.pack_default_value();

    } else {
      const FieldData &fd = cls_data->_fields[field_idx];
      switch (fd._type) {
      case FieldData::FT_int:
        packer.pack_int(*(int *)(object + fd._offset));
        break;
      case FieldData::FT_uint:
        packer.pack_uint(*(unsigned int *)(object + fd._offset));
        break;
      case FieldData::FT_double:
        packer.pack_double(*(double *)(object + fd._offset));
        break;
      case FieldData::FT_float:
        packer.pack_double(*(float *)(object + fd._offset));
        break;
      case FieldData::FT_int64:
        packer.pack_int64(*(int64_t *)(object + fd._offset));
        break;
      case FieldData::FT_uint64:
        packer.pack_uint64(*(uint64_t *)(object + fd._offset));
        break;
      case FieldData::FT_string:
        packer.pack_string(*(std::string *)(object + fd._offset));
        break;
      case FieldData::FT_vec2f:
        {
          const LVecBase2f &vec = *(const LVecBase2f *)(object + fd._offset);
          packer.pack_double(vec[0]);
          packer.pack_double(vec[1]);
        }
        break;
      case FieldData::FT_vec3f:
        {
          const LVecBase3f &vec = *(const LVecBase3f *)(object + fd._offset);
          packer.pack_double(vec[0]);
          packer.pack_double(vec[1]);
          packer.pack_double(vec[2]);
        }
        break;
      case FieldData::FT_vec4f:
        {
          const LVecBase4f &vec = *(const LVecBase4f *)(object + fd._offset);
          packer.pack_double(vec[0]);
          packer.pack_double(vec[1]);
          packer.pack_double(vec[2]);
          packer.pack_double(vec[3]);
        }
        break;
      default:
        assert(false);
        break;
      }
    }

    if (!packer.end_pack()) {
      std::cerr << "Failed to pack field " << field->get_name() << "\n";
    }
  }

  object = (unsigned char *)&recv_obj;
  DCPacker unpack;
  unpack.set_unpack_data(packer.get_data(), packer.get_length(), false);
  for (int i = 0; i < dclass->get_num_inherited_fields(); i++) {
    DCField *field = dclass->get_inherited_field(i);

    unpack.begin_unpack(field);

    int field_idx = -1;
    for (int j = 0; j < cls_data->_fields.size(); j++) {
      if (cls_data->_fields[j]._name == field->get_name()) {
        field_idx = j;
        break;
      }
    }

    if (field_idx == -1) {
      unpack.unpack_skip();

    } else {
      const FieldData &fd = cls_data->_fields[field_idx];
      switch (fd._type) {
      case FieldData::FT_int:
        *(int *)(object + fd._offset) = unpack.unpack_int();
        break;
      case FieldData::FT_uint:
        *(unsigned int *)(object + fd._offset) = unpack.unpack_uint();
        break;
      case FieldData::FT_double:
        *(double *)(object + fd._offset) = unpack.unpack_double();
        break;
      case FieldData::FT_float:
        *(float *)(object + fd._offset) = unpack.unpack_double();
        break;
      case FieldData::FT_int64:
        *(int64_t *)(object + fd._offset) = unpack.unpack_int64();
        break;
      case FieldData::FT_uint64:
        *(uint64_t *)(object + fd._offset) = unpack.unpack_uint64();
        break;
      case FieldData::FT_string:
        *(std::string *)(object + fd._offset) = unpack.unpack_string();
        break;
      default:
        assert(false);
        break;
      }
    }

    if (!unpack.end_unpack()) {
      std::cerr << "Failed to unpack field " << field->get_name() << "\n";
    }
  }

  std::cout << "foo = " << recv_obj._foo << "\n";
  std::cout << "bar = " << recv_obj._bar << "\n";
  std::cout << "name = " << recv_obj._name << "\n";

  return 0;
}

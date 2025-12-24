#include "vectorNetClasses.h"

#include "luse.h"

NetworkClass *Position_NetClass = nullptr;
NetworkClass *UnitVector_NetClass = nullptr;
NetworkClass *Angles_NetClass = nullptr;
NetworkClass *Quat_NetClass = nullptr;
NetworkClass *Scale_NetClass = nullptr;

template<typename T>
static void *fetch_vec_ptr(void *obj) {
  return (void *)((T *)obj)->get_data();
}

template<typename T>
static void fetch_vec_x(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_x();
}

template<typename T>
static void fetch_vec_y(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_y();
}

template<typename T>
static void fetch_vec_z(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_z();
}

template<typename T>
static void fetch_vec_w(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_w();
}

// Sets up network class definitions for various encodings of Panda vectors
// representing different things, eg, positions, angles, quat, unit vectors, etc.
void
init_vector_net_classes() {
  if (Position_NetClass == nullptr) {
    Position_NetClass = new NetworkClass("Position");
    Position_NetClass->set_stride(sizeof(LVecBase3f));
    // Just define it as a 3 float array.
    NetworkField *field = new NetworkField;
    field->name = "data";
    field->offset = 0;
    field->source_type = NetworkField::DT_float;
    field->encoding_type = NetworkField::DT_float;
    field->count = 3;
    field->stride = sizeof(float);
    Position_NetClass->add_field(field);
    NetworkClassRegistry::ptr()->register_class(Position_NetClass);
  }

  if (UnitVector_NetClass == nullptr) {
    UnitVector_NetClass = new NetworkClass("UnitVector");
    UnitVector_NetClass->set_stride(sizeof(LVecBase3f));
    NetworkField *field = new NetworkField;
    field->name = "data";
    field->offset = 0;
    field->count = 3;
    field->source_type = NetworkField::DT_float;
    field->encoding_type = NetworkField::DT_int16;
    field->divisor = 1000;
    field->stride = sizeof(float);
    UnitVector_NetClass->add_field(field);
    NetworkClassRegistry::ptr()->register_class(UnitVector_NetClass);
  }

  if (Angles_NetClass == nullptr) {
    Angles_NetClass = new NetworkClass("Angles");
    Angles_NetClass->set_stride(sizeof(LVecBase3f));
    NetworkField *field = new NetworkField;
    field->name = "data";
    field->offset = 0;
    field->count = 3;
    field->source_type = NetworkField::DT_float;
    field->encoding_type = NetworkField::DT_int16;
    field->divisor = 10;
    field->modulo = 360;
    field->stride = sizeof(float);
    Angles_NetClass->add_field(field);
    NetworkClassRegistry::ptr()->register_class(Angles_NetClass);
  }

  if (Quat_NetClass == nullptr) {
    Quat_NetClass = new NetworkClass("Quat");
    Quat_NetClass->set_stride(sizeof(LQuaternionf));
    NetworkField *field = new NetworkField;
    field->name = "data";
    field->offset = 0;
    field->count = 4;
    field->source_type = NetworkField::DT_float;
    field->encoding_type = NetworkField::DT_int16;
    field->divisor = 10000;
    field->stride = sizeof(float);
    Quat_NetClass->add_field(field);
    NetworkClassRegistry::ptr()->register_class(Quat_NetClass);
  }

  if (Scale_NetClass == nullptr) {
    Scale_NetClass = new NetworkClass("Scale");
    Scale_NetClass->set_stride(sizeof(LVecBase3f));
    NetworkField *field = new NetworkField;
    field->name = "data";
    field->offset = 0;
    field->count = 3;
    field->source_type = NetworkField::DT_float;
    field->encoding_type = NetworkField::DT_int16;
    field->divisor = 1000;
    field->stride = sizeof(float);
    Scale_NetClass->add_field(field);
    NetworkClassRegistry::ptr()->register_class(Scale_NetClass);
  }
}

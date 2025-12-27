#include "vectorNetClasses.h"

#include "lvecBase4.h"
#include "networkClass.h"

template<typename T>
static void *
fetch_vec_ptr(void *obj) {
  return (void *)((T *)obj)->get_data();
}

template<typename T>
static void
fetch_vec_x(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_x();
}

template<typename T>
static void
fetch_vec_y(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_y();
}

template<typename T>
static void
fetch_vec_z(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_z();
}

template<typename T>
static void
fetch_vec_w(void *obj, void *dest) {
  *(float *)dest = ((T *)obj)->get_w();
}

template<typename T>
static void
write_vec_x(void *object, void *data) {
  ((T *)object)->set_x(*(float *)data);
}

template<typename T>
static void
write_vec_y(void *object, void *data) {
  ((T *)object)->set_y(*(float *)data);
}

template<typename T>
static void
write_vec_z(void *object, void *data) {
  ((T *)object)->set_z(*(float *)data);
}

template<typename T>
static void
write_vec_w(void *object, void *data) {
  ((T *)object)->set_w(*(float *)data);
}

NetworkClass *Position_NetClass::_network_class = nullptr;
NetworkClass *UnitVector_NetClass::_network_class = nullptr;
NetworkClass *Quat_NetClass::_network_class = nullptr;
NetworkClass *Scale_NetClass::_network_class = nullptr;
NetworkClass *Angles_NetClass::_network_class = nullptr;

/**
 * 
 */
void
Position_NetClass::init_network_class() {
  BEGIN_NETWORK_CLASS_NOBASE(Position_NetClass);
  MAKE_INDIRECT_NET_FIELD(float, x, fetch_vec_x<LVecBase3f>,
                          write_vec_x<LVecBase3f>, NetworkField::DT_float);
  MAKE_INDIRECT_NET_FIELD(float, y, fetch_vec_y<LVecBase3f>,
                          write_vec_y<LVecBase3f>, NetworkField::DT_float);
  MAKE_INDIRECT_NET_FIELD(float, z, fetch_vec_z<LVecBase3f>,
                          write_vec_z<LVecBase3f>, NetworkField::DT_float);
  END_NETWORK_CLASS();
}

/**
 * 
 */
void
UnitVector_NetClass::init_network_class() {
  BEGIN_NETWORK_CLASS_NOBASE(UnitVector_NetClass);
  MAKE_INDIRECT_NET_FIELD(float, x, fetch_vec_x<LVecBase3f>,
                          write_vec_x<LVecBase3f>, NetworkField::DT_int16,
                          1000);
  MAKE_INDIRECT_NET_FIELD(float, y, fetch_vec_y<LVecBase3f>,
                          write_vec_y<LVecBase3f>, NetworkField::DT_int16,
                          1000);
  MAKE_INDIRECT_NET_FIELD(float, z, fetch_vec_z<LVecBase3f>,
                          write_vec_z<LVecBase3f>, NetworkField::DT_int16,
                          1000);
  END_NETWORK_CLASS();
}

/**
 * 
 */
void
Scale_NetClass::init_network_class() {
  BEGIN_NETWORK_CLASS_NOBASE(Scale_NetClass);
  MAKE_INDIRECT_NET_FIELD(float, x, fetch_vec_x<LVecBase3f>,
                          write_vec_x<LVecBase3f>, NetworkField::DT_int16,
                          1000);
  MAKE_INDIRECT_NET_FIELD(float, y, fetch_vec_y<LVecBase3f>,
                          write_vec_y<LVecBase3f>, NetworkField::DT_int16,
                          1000);
  MAKE_INDIRECT_NET_FIELD(float, z, fetch_vec_z<LVecBase3f>,
                          write_vec_z<LVecBase3f>, NetworkField::DT_int16,
                          1000);
  END_NETWORK_CLASS();
}

/**
 * 
 */
void
Angles_NetClass::init_network_class() {
  BEGIN_NETWORK_CLASS_NOBASE(Angles_NetClass);
  MAKE_INDIRECT_NET_FIELD(float, x, fetch_vec_x<LVecBase3f>,
                          write_vec_x<LVecBase3f>, NetworkField::DT_int16, 10,
                          360);
  MAKE_INDIRECT_NET_FIELD(float, y, fetch_vec_y<LVecBase3f>,
                          write_vec_y<LVecBase3f>, NetworkField::DT_int16, 10,
                          360);
  MAKE_INDIRECT_NET_FIELD(float, z, fetch_vec_z<LVecBase3f>,
                          write_vec_z<LVecBase3f>, NetworkField::DT_int16, 10,
                          360);
  END_NETWORK_CLASS();
}

/**
 * 
 */
void
Quat_NetClass::init_network_class() {
  BEGIN_NETWORK_CLASS_NOBASE(Quat_NetClass);
  MAKE_INDIRECT_NET_FIELD(float, x, fetch_vec_x<LVecBase4f>,
                          write_vec_x<LVecBase4f>, NetworkField::DT_int16,
                          10000);
  MAKE_INDIRECT_NET_FIELD(float, y, fetch_vec_y<LVecBase4f>,
                          write_vec_y<LVecBase4f>, NetworkField::DT_int16,
                          10000);
  MAKE_INDIRECT_NET_FIELD(float, z, fetch_vec_z<LVecBase4f>,
                          write_vec_z<LVecBase4f>, NetworkField::DT_int16,
                          10000);
  MAKE_INDIRECT_NET_FIELD(float, w, fetch_vec_w<LVecBase4f>,
                          write_vec_w<LVecBase4f>, NetworkField::DT_int16,
                          10000);
  END_NETWORK_CLASS();
}

/**
 * 
 */
void
init_vector_net_classes() {
  Position_NetClass::init_network_class();
  Angles_NetClass::init_network_class();
  Scale_NetClass::init_network_class();
  UnitVector_NetClass::init_network_class();
  Quat_NetClass::init_network_class();
}

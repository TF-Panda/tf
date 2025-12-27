#ifndef VECTORNETCLASSES_H
#define VECTORNETCLASSES_H

// This files contains network class definitions for different encodings of
// Panda vectors, depending on how the vector is used.

#include "luse.h"
#include "networkClass.h"

void init_vector_net_classes();

/**
 * Defines rules for encoding a Vec3 as a position over the wire.
 */
class Position_NetClass : LVecBase3f {
public:
  static void init_network_class();
  inline static NetworkClass *get_network_class() {
    return _network_class;
  }

private:
  static NetworkClass *_network_class;
};

/**
 * Defines rules for encoding a Vec3 as a unit vector over the wire.
 */
class UnitVector_NetClass : LVecBase3f {
public:
  static void init_network_class();
  inline static NetworkClass *get_network_class() {
    return _network_class;
  }

private:
  static NetworkClass *_network_class;
};

/**
 * Defines rules for encoding a Vec3 as a scale over the wire.
 */
class Scale_NetClass : LVecBase3f {
public:
  static void init_network_class();
  inline static NetworkClass *get_network_class() {
    return _network_class;
  }

private:
  static NetworkClass *_network_class;
};

/**
 * Defines rules for encoding an Vec4 as a quaternion over the wire.
 */
class Quat_NetClass : LVecBase4f {
public:
  static void init_network_class();
  inline static NetworkClass *get_network_class() {
    return _network_class;
  }

private:
  static NetworkClass *_network_class;
};

/**
 * Defines rules for encoding a Vec3 as Euler angles over the wire.
 */
class Angles_NetClass : LVecBase3f {
public:
  static void init_network_class();
  inline static NetworkClass *get_network_class() {
    return _network_class;
  }

private:
  static NetworkClass *_network_class;  
};

#endif  // VECTORNETCLASSES_H

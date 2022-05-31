/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file py_interface.cxx
 * @author brian
 * @date 2022-05-25
 */

#include "py_interface.h"

Dtool_PyTypedObject *py_vec2_type = nullptr;
Dtool_PyTypedObject *py_vec3_type = nullptr;
Dtool_PyTypedObject *py_vec4_type = nullptr;
bool py_types_initialized = false;

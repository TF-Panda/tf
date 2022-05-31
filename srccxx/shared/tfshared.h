/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfshared.h
 * @author brian
 * @date 2022-05-12
 */

#ifndef TFSHARED_H
#define TFSHARED_H

#include "tfbase.h"

#ifdef TF_CLIENT
#define CLP(x) x
#else // server
#define CLP(x) x##AI
#endif

#endif // TFSHARED_H

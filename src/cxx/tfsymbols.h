/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file tfsymbols.h
 * @author brian
 * @date 2022-05-23
 */

#ifndef TFSYMBOLS_H
#define TFSYMBOLS_H

#ifdef BUILDING_TF_CXX
  #define EXPCL_TF_CXX EXPORT_CLASS
  #define EXPTP_TF_CXX EXPORT_TEMPL
#else
  #define EXPCL_TF_CXX IMPORT_CLASS
  #define EXPTP_TF_CXX IMPORT_TEMPL
#endif

#endif // TFSYMBOLS_H

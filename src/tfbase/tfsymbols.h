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
 * @date 2022-05-10
 */

#ifndef TFSYMBOLS_H
#define TFSYMBOLS_H

/* See dtoolsymbols.h for a rant on the purpose of this file.  */

#ifdef BUILDING_TF_DISTRIBUTED
  #define EXPCL_TF_DISTRIBUTED EXPORT_CLASS
  #define EXPTP_TF_DISTRIBUTED EXPORT_TEMPL
#else
  #define EXPCL_TF_DISTRIBUTED IMPORT_CLASS
  #define EXPTP_TF_DISTRIBUTED IMPORT_TEMPL
#endif

#endif // TFSYMBOLS_H

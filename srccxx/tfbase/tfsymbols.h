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
 * @date 2021-11-11
 */

/* See dtoolsymbols.h for a rant on the purpose of this file.  */

#ifndef TFSYMBOLS_H
#define TFSYMBOLS_H

#if defined(BUILDING_TF_CLIENT) || defined(BUILDING_TF_SERVER)
  #define EXPCL_TF_GAME EXPORT_CLASS
  #define EXPTP_TF_GAME EXPORT_TEMPL
#else
  #define EXPCL_TF_GAME IMPORT_CLASS
  #define EXPTP_TF_GAME IMPORT_TEMPL
#endif

#ifdef BUILDING_TF_TFBASE
  #define EXPCL_TF_TFBASE EXPORT_CLASS
  #define EXPTP_TF_TFBASE EXPORT_TEMPL
#else
  #define EXPCL_TF_TFBASE IMPORT_CLASS
  #define EXPTP_TF_TFBASE IMPORT_TEMPL
#endif

#endif // TFSYMBOLS_H

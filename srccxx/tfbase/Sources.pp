#define OTHER_LIBS interrogatedb \
                   dtoolutil:c dtoolbase:c dtool:m prc \
                   panda:m pgraphnodes:c pgraph:c linmath:c \
                   event:c gobj:c

#begin lib_target
  #define TARGET tfbase

  #define BUILDING_DLL BUILDING_TF_TFBASE

  #define SOURCES \
    config_tfbase.h \
    tfbase.h tfsymbols.h

  #define COMPOSITE_SOURCES \
    config_tfbase.cxx

  #define INSTALL_HEADERS \
    config_tfbase.h \
    tfbase.h tfsymbols.h

  #define IGATESCAN all

#end lib_target

#begin bin_target
  #define OTHER_LIBS $[OTHER_LIBS] dcparser:c direct:m
  #define TARGET test-dc-rttr
  #define SOURCES test_dc_rttr.cxx
  #define C++FLAGS $[C++FLAGS] -DWITHIN_PANDA
#end bin_target

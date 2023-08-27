#begin lib_target
  #define TARGET tf
  #define BUILDING_DLL BUILDING_TF_CXX
  #define OTHER_LIBS \
    dtool:m dtoolbase:c dtoolutil:c prc interrogatedb \
    pandaexpress:m express:c downloader:c gobj:c pgraph:c pipeline:c \
    panda:m putil:c linmath:c pstatclient:c parametrics:c mathutil:c
  #define USE_PACKAGES eigen

  #define SOURCES \
    config_tf.h config_tf.cxx \
    tfbase.h tfsymbols.h \
    quickRopeNode.h quickRopeNode.I quickRopeNode.cxx \
    ropePhysics.h ropePhysics.I ropePhysics.cxx \

  #define IGATESCAN all
  #define IGATEEXT prediction.h prediction.I prediction.cxx

#end lib_target

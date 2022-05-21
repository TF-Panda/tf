#begin interface_target
  #define TARGET tfshared
  #define SOURCES \
    distributedEntity_src.h distributedEntity_src.I distributedEntity_src.cxx \
    gameLevel_src.h gameLevel_src.I gameLevel_src.cxx \
    netMessages.h \
    tfGlobals.h \
    tfshared.h

#end interface_target

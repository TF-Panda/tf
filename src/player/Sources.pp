#begin lib_target
  #define TARGET player
  #define BUILDING_DLL BUILDING_TF_PLAYER
  #define LOCAL_LIBS tfbase
  #define OTHER_LIBS \
    dtool:m dtoolbase:c dtoolutil:c prc interrogatedb \
    pandaexpress:m express:c downloader:c \
    panda:m putil:c linmath:c pstatclient:c
  #define USE_PACKAGES eigen

  #define SOURCES \
    config_player.h config_player.cxx
  #define IGATESCAN all
  #define IGATEEXT prediction.h prediction.I prediction.cxx
#end lib_target

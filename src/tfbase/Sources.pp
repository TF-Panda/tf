#define OTHER_LIBS dtool:m dtoolbase:c dtoolutil:c prc panda:m \
    express:c putil:c linmath:c mathutil:c pgraph:c pgraphnodes:c \
    display:c gobj:c pipeline:c event:c audio:c postprocess:c anim:c \
    shader:c pandaexpress:m downloader:c pdx:c map:c
#define USE_PACKAGES eigen sleef valve_steamnet

#begin interface_target
  #define TARGET tfbase
  #define SOURCES \
    tfbase.h tfsymbols.h

#end interface_target

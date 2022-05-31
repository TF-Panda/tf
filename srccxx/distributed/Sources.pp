#begin lib_target
  #define TARGET tfdistributed
  #define LOCAL_LIBS tfbase
  #define OTHER_LIBS dtool:m dtoolbase:c dtoolutil:c prc panda:m \
    express:c putil:c linmath:c mathutil:c pgraph:c pgraphnodes:c \
    display:c gobj:c pipeline:c event:c audio:c postprocess:c anim:c \
    shader:c pandaexpress:m downloader:c nativenet:c steamnet:c pstatclient:c \
    net:c pphysics:c pdx:c
  #define USE_PACKAGES physx
  #define BUILDING_DLL BUILDING_TF_DISTRIBUTED
  #define SOURCES \
    actor.h actor.I actor.cxx \
    appBase.h appBase.I appBase.cxx \
    config_tfdistributed.h config_tfdistributed.cxx \
    model.h model.I model.cxx \
    networkClass.h networkClass.I networkClass.cxx \
    networkedObjectBase.h networkedObjectBase.I networkedObjectBase.cxx \
    networkedObjectRegistry.h networkedObjectRegistry.I networkedObjectRegistry.cxx \
    networkField.h networkField.I networkField.cxx \
    networkRepository.h networkRepository.I networkRepository.cxx \
    playerCommand.h playerCommand.I playerCommand.cxx \
    simulationManager.h simulationManager.I simulationManager.cxx
#end lib_target


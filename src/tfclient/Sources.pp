#define LOCAL_LIBS tfbase tfshared tfdistributed

#define OTHER_LIBS pdx:c map:c material:c

#begin bin_target
  #define TARGET tfclient
  #define SOURCES \
    config_tfclient.h config_tfclient.cxx \
    clientRepository.h clientRepository.I clientRepository.cxx \
    distributedGame.h distributedGame.I distributedGame.cxx \
    distributedObject.h distributedObject.I distributedObject.cxx \
    gameLevel.h gameLevel.cxx \
    tfclient_main.cxx \
    tfclient_types.h tfclient_types.cxx \
    tfClientBase.h tfClientBase.I tfClientBase.cxx
  #define C++FLAGS $[C++FLAGS] -DTF_CLIENT

#end bin_target

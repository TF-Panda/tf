
#define SHARED_SOURCES \
  netMessages.h \
  networkClass.h networkClass.cxx \
  networkClasses.h networkClasses.cxx \
  networkClassRegistry.h networkClassRegistry.cxx \
  networkField.h networkField.cxx \
  networkObject.h networkObject.cxx \
  networkRPC.h networkRPC.cxx \
  vectorNetClasses.h vectorNetClasses.cxx

#define OTHER_LIBS dtool:m panda:m display:c pgraph:c pgraphnodes:c \
  dtoolbase:c dtoolutil:c pipeline:c linmath:c mathutil:c express:c \
  putil:c gobj:c device:c dgraph:c tform:c prc map:c shader:c event:c \
  pphysics:c anim:c audio:c

#define USE_PACKAGES physx

// TF2 client binary.
#begin bin_target
  #define TARGET tf-client
  #define C++FLAGS $[C++FLAGS] -DCLIENT
  #define SOURCES \
    $[SHARED_SOURCES] \
    client/main.cxx \
    client/inputManager.h client/inputManager.I client/inputManager.cxx \
    client/globals.h client/globals.cxx
#end bin_target

// TF2 server binary.
#begin bin_target
  #define TARGET tf-server
  #define C++FLAGS $[C++FLAGS] -DSERVER
  #define SOURCES \
    $[SHARED_SOURCES] \
    server/main_server.cxx \
    server/server.h server/server.cxx
#end bin_target
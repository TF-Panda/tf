// Libraries from the engine we need to link with.
#define OTHER_LIBS dtool:m panda:m display:c pgraph:c pgraphnodes:c \
  dtoolbase:c dtoolutil:c pipeline:c linmath:c mathutil:c express:c \
  putil:c gobj:c device:c dgraph:c tform:c prc map:c shader:c event:c \
  pphysics:c anim:c audio:c steamnet:c net:c grutil:c text:c gsgbase:c \
  display:c nativenet:c

// Third party packages we need to bring in.
#define USE_PACKAGES physx valve_steamnet

#if $[or $[eq $[USE_COMPILER], Clang], $[eq $[USE_COMPILER], GCC]]
// For the network field system, we use offsetof to determine the
// address of networked fields on entities.  All of our networked
// class types are non-standard layout (use inheritance, have a vtable, etc),
// but the compiler gives us proper offsets regardless.  We just have to not
// use multiple inheritance on any networked classes.
#define C++FLAGS $[C++FLAGS] -Wno-invalid-offsetof
#endif

//
// Sources compiled on both the server and client binaries.
//
#define SHARED_SOURCES \
  netMessages.h \
  networkClass.h networkClass.cxx \
  networkClasses.h networkClasses.cxx \
  networkClassRegistry.h networkClassRegistry.cxx \
  networkField.h networkField.cxx \
  networkObject.h networkObject.cxx \
  networkRPC.h networkRPC.cxx \
  vectorNetClasses.h vectorNetClasses.cxx \
  simulationManager.h simulationManager.cxx \
  gameManager.h gameManager.cxx \
  gameGlobals.h gameGlobals.cxx \
  tfPlayer.h tfPlayer.cxx \
  entity.h entity.cxx \
  playerCommand.h playerCommand.cxx \
  gameEnums.h \
  weapon.h weapon.cxx \
  viewModel.h viewModel.cxx

// TF2 client binary.
#begin bin_target
  #define TARGET tf-client

  #define C++FLAGS $[C++FLAGS] -DCLIENT

  #define CLIENT_SOURCES \
    main.cxx \
    inputManager.h inputManager.I inputManager.cxx \
    client.h client.cxx \
    client_config.h client_config.cxx \
    localTFPlayer.h localTFPlayer.cxx \
    prediction.h prediction.cxx \
    sounds.h sounds.cxx

  #define SOURCES \
    $[SHARED_SOURCES] \
    $[matrix client/,$[CLIENT_SOURCES]]

#end bin_target

// TF2 server binary.
#begin bin_target
  #define TARGET tf-server

  #define C++FLAGS $[C++FLAGS] -DSERVER

  #define SERVER_SOURCES \
    main_server.cxx \
    server.h server.cxx \
    networkSnapshotManager.h networkSnapshotManager.cxx \
    tfPlayerAI.cxx

  #define SOURCES \
    $[SHARED_SOURCES] \
    $[matrix server/,$[SERVER_SOURCES]]

#end bin_target
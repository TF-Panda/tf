
#begin bin_target
  #define OTHER_LIBS dtool:m panda:m display:c pgraph:c pgraphnodes:c dtoolbase:c dtoolutil:c pipeline:c linmath:c mathutil:c express:c putil:c gobj:c device:c dgraph:c tform:c prc map:c shader:c event:c pphysics:c anim:c audio:c
  #define USE_PACKAGES physx
  #define TARGET prog
  #define SOURCES \
    main.cxx \
    entity.cxx entity.h entity.I \
    entityFactory.cxx entityFactory.h entityFactory.I \
    player.cxx player.h player.I \
    inputManager.cxx inputManager.h inputManager.I \
    globals.h globals.cxx \
    world.cxx world.h world.I
#end bin_target

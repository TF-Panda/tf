#define LOCAL_LIBS tfbase tfshared tfdistributed

#define OTHER_LIBS pdx:c map:c

#begin bin_target
  #define TARGET tfai
  #define SOURCES \
    changeFrameList.h changeFrameList.I changeFrameList.cxx \
    clientFrame.h clientFrame.I clientFrame.cxx \
    clientFrameManager.h clientFrameManager.I clientFrameManager.cxx \
    clientInfo.h clientInfo.I clientInfo.cxx \
    config_tfai.h config_tfai.cxx \
    distributedEntityAI.h distributedEntityAI.cxx \
    distributedGameAI.h distributedGameAI.I distributedGameAI.cxx \
    distributedObjectAI.h distributedObjectAI.cxx \
    frameSnapshot.h frameSnapshot.I frameSnapshot.cxx \
    frameSnapshotEntry.h frameSnapshotEntry.I frameSnapshotEntry.cxx \
    frameSnapshotManager.h frameSnapshotManager.I frameSnapshotManager.cxx \
    gameLevelAI.h gameLevelAI.cxx \
    packedObject.h packedObject.I packedObject.cxx \
    serverRepository.h serverRepository.I serverRepository.cxx \
    tfai_main.cxx \
    tfai_netclasses.h tfai_netclasses.cxx \
    tfai_types.h tfai_types.cxx \
    tfAIBase.h tfAIBase.I tfAIBase.cxx
  #define C++FLAGS $[C++FLAGS] -DTF_SERVER

#end bin_target

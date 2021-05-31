from enum import IntEnum, auto, IntFlag

class AnimEventType(IntFlag):

    Invalid = 0

    Server = 1 << 0
    Client = 1 << 1
    Client_Server = (Server | Client)

class AnimEvent(IntEnum):

    Invalid = -1

    Client_Play_Sound = auto()

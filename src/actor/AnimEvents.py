
class AnimEventType:

    Invalid = 0

    Server = 1 << 0
    Client = 1 << 1
    Client_Server = (Server | Client)

from panda3d.core import AnimEvent as AE
AnimEvent = AE.ptr()

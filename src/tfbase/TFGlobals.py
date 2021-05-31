UberZone = 1
GameZone = 2

from enum import IntEnum, IntFlag
from panda3d.core import BitMask32

class CollisionGroup(IntEnum):
    Empty = 0
    Debris = 1
    InteractiveDebris = 2
    Interactive = 3
    Player = 4
    PlayerMovement = 5

class Contents(IntFlag):
    Empty = 0
    Solid = 1 << 0
    RedTeam = 1 << 1
    BlueTeam = 1 << 2
    HitBox = 1 << 3

# Non-entity parent codes
class WorldParent(IntEnum):
    Unchanged = -1 # Don't change the parent, allow client code to parent and whatever.
    Render = -2 # Parent into 3D scene root.
    Hidden = -3 # Don't render.
    ViewModel = -4 # Parent into view model scene.
    ViewModelCamera = -5 # Parent to view model scene camera.
    Camera = -6 # Parent to 3D scene camera.

def getWorldParent(parentId):
    """
    Returns parent node from world parent ID.
    """
    if parentId == WorldParent.Unchanged:
        return None
    elif parentId == WorldParent.Render:
        return base.render
    elif parentId == WorldParent.Hidden:
        return base.hidden
    elif parentId == WorldParent.ViewModel:
        return base.vmRender
    elif parentId == WorldParent.ViewModelCamera:
        return base.vmCamera
    elif parentId == WorldParent.Camera:
        return base.camera
    else:
        return None

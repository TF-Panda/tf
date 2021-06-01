###############################################################################
# Game network locations.

# We always have interest in the uber zone.  Objects/entities here are
# omnipresent.  Examples of objects that would live in the uber zone are the
# game manager, global services, etc.
UberZone = 1

# This is temporary.  Want to implement a PVS/room zoning system based on
# level partitioning structure.
GameZone = 2

###############################################################################

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

# Different damage types and options.  Taken from shareddefs.h.  Most of them
# are unused by TF, but I put all of them here anyways.
class DamageType(IntFlag):
    Generic                 = 0
    Crush                   = (1 << 0)
    Bullet                  = (1 << 1)
    Slash                   = (1 << 2)
    Burn                    = (1 << 3)
    Vehicle                 = (1 << 4)
    Fall                    = (1 << 5)
    Blast                   = (1 << 6)
    Club                    = (1 << 7)
    Shock                   = (1 << 8)
    Sonic                   = (1 << 9)
    EnergyBeam              = (1 << 10)
    PreventPhysicsForce     = (1 << 11)
    NeverGib                = (1 << 12)
    Drown                   = (1 << 13)
    Paralyze                = (1 << 14)
    NerveGas                = (1 << 15)
    Poison                  = (1 << 16)
    Radiation               = (1 << 17)
    DrownRecover            = (1 << 18)
    Acid                    = (1 << 19)
    SlowBurn                = (1 << 20)
    RemoveNoRagdoll         = (1 << 21)
    PhysGun                 = (1 << 22)
    Plasma                  = (1 << 23)
    Airboat                 = (1 << 24)
    Dissolve                = (1 << 25)
    BlastSurface            = (1 << 26)
    Direct                  = (1 << 27)
    Buckshot                = (1 << 28)

    # TF-specific ones.  They re-use the unused HL2 ones up there.
    UseHitLocations         = Airboat
    HalfFalloff             = Radiation
    Critical                = Acid
    RadiusMax               = EnergyBeam
    Ignite                  = Plasma
    UseDistanceMod          = SlowBurn
    NoCloseDistanceMod      = Poison
    IgnoreMaxHealth         = Bullet

class TakeDamage(IntEnum):
    No          = 0
    EventsOnly  = 1
    Yes         = 2
    Aim         = 3

def simpleSpline(value):
    valueSquared = value * value
    return (3 * valueSquared - 2 * valueSquared * value)

def remapValClamped(val, A, B, C, D):
    if A == B:
        return D if val >= B else C

    cVal = (val - A) / (B - A)
    cVal = max(0.0, min(1.0, cVal))
    return C + (D - C) * cVal

def simpleSplineRemapValClamped(val, A, B, C, D):
    if A == B:
        return D if val >= B else C

    cVal = (val - A) / (B - A)
    cVal = max(0.0, min(1.0, cVal))
    return C + (D - C) * simpleSpline(cVal)

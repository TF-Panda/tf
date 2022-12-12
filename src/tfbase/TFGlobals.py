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

from panda3d.core import BitMask32, Vec3, DynamicTextFont, SamplerState, NodePath, LineSegs

class SpeechConcept:

    TakeDamage = 0
    Killed = 1

    MedicCall = 2
    HelpMe = 3
    Thanks = 4
    BattleCry = 5
    Incoming = 6
    GoodJob = 7
    NiceShot = 8
    Cheers = 9
    Positive = 10
    Jeers = 11
    Negative = 12
    SentryHere = 13
    TeleporterHere = 14
    DispenserHere = 15
    SentryAhead = 16
    ChargeReady = 17
    ActivateCharge = 18
    Yes = 19
    No = 20
    Go = 21
    MoveUp = 22
    GoLeft = 23
    GoRight = 24
    SpyIdentify = 25

    WeaponFire = 26

    CappedObjective = 27
    RoundEnd = 28
    RoundStart = 29

    ObjectBuilding = 30
    ObjectMoving = 31
    ObjectReplace = 32
    ObjectBeingSapped = 33
    ObjectDestroyed = 34

    KilledPlayer = 35
    KilledObject = 36

    Teleported = 37
    StoppedBeingHealed = 38

class TFTeam:
    NoTeam = -1
    Red = 0
    Blue = 1

    COUNT = 2

class SolidShape:
    Empty = 0 # Nothing.
    Box = 1 # Bounding box.
    Sphere = 2 # Bounding sphere.
    Model = 3 # Use model collision mesh data.

class SolidFlag:
    Intangible = 0
    Tangible = 1 << 0
    Trigger = 1 << 1

# Non-entity parent codes
class WorldParent:
    Unchanged = -1 # Don't change the parent, allow client code to parent and whatever.
    Render = -2 # Parent into 3D scene root.
    Hidden = -3 # Don't render.
    ViewModel = -4 # Parent into view model scene.
    ViewModelCamera = -5 # Parent to view model scene camera.
    Camera = -6 # Parent to 3D scene camera.
    DynRender = -7
    SkyBox = -8

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
    elif parentId == WorldParent.DynRender:
        return base.dynRender
    elif parentId == WorldParent.SkyBox:
        return base.sky3DRoot
    else:
        return None

# Different damage types and options.  Taken from shareddefs.h.  Most of them
# are unused by TF, but I put all of them here anyways.
class DamageType:
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

class TakeDamage:
    No          = 0
    EventsOnly  = 1
    Yes         = 2
    Aim         = 3

def simpleSpline(value):
    valueSquared = value * value
    return (3 * valueSquared - 2 * valueSquared * value)

def remapVal(val, A, B, C, D):
    if A == B:
        return D if val >= B else C

    cVal = (val - A) / (B - A)
    return C + (D - C) * cVal

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

def angleMod(a):
    a = (360.0/65536) * (int(a*(65536.0/360.0)) & 65535)
    return a

def approach(target, value, speed):
    delta = target - value
    if delta > speed:
        value += speed
    elif delta < -speed:
        value -= speed
    else:
        value = target

    return value

def approachAngle(target, value, speed):
    target = angleMod(target)
    value = angleMod(value)

    delta = target - value

    if speed < 0:
        speed = -speed

    if delta < -180:
        delta += 360
    elif delta > 180:
        delta -= 360

    if delta > speed:
        value += speed
    elif delta < -speed:
        value -= speed
    else:
        value = target

    return value

def configureFont(fnt, ppu=48):
    fnt.setPixelsPerUnit(ppu)
    fnt.setNativeAntialias(True)
    fnt.setAnisotropicDegree(16)
    fnt.setTextureMargin(4)

TF2Font = None
def getTF2Font():
    global TF2Font
    if not TF2Font:
        TF2Font = DynamicTextFont("models/fonts/TF2.ttf")
        configureFont(TF2Font)
    return TF2Font

TF2BuildFont = None
def getTF2BuildFont():
    global TF2BuildFont
    if not TF2BuildFont:
        TF2BuildFont = DynamicTextFont("models/fonts/tf2build.ttf")
        configureFont(TF2BuildFont, 128)
    return TF2BuildFont

TF2SecondaryFont = None
def getTF2SecondaryFont():
    global TF2SecondaryFont
    if not TF2SecondaryFont:
        TF2SecondaryFont = DynamicTextFont("models/fonts/TF2secondary.ttf")
        configureFont(TF2SecondaryFont)
    return TF2SecondaryFont

TF2ProfessorFont = None
def getTF2ProfessorFont():
    global TF2ProfessorFont
    if not TF2ProfessorFont:
        TF2ProfessorFont = DynamicTextFont("models/fonts/tf2professor.ttf")
        configureFont(TF2ProfessorFont)
    return TF2ProfessorFont

def getAxisViz():
    segs = LineSegs('axis')
    segs.setColor((0, 1, 0, 1))
    segs.moveTo((0, 0, 0))
    segs.drawTo((0, 16, 0))
    segs.setColor((1, 0, 0, 1))
    segs.moveTo((0, 0, 0))
    segs.drawTo((16, 0, 0))
    segs.setColor((0, 0, 1, 1))
    segs.moveTo((0, 0, 0))
    segs.drawTo((0, 0, 16))
    return NodePath(segs.create())

def getBoxViz(mins, maxs, thickness, color):
    segs = LineSegs('box')
    segs.setThickness(thickness)
    segs.setColor(color)
    # Bottom face.
    segs.moveTo(mins)
    segs.drawTo(mins.x, maxs.y, mins.z)
    segs.drawTo(maxs.x, maxs.y, mins.z)
    segs.drawTo(maxs.x, mins.y, mins.z)
    segs.drawTo(mins)
    # Top face.
    segs.moveTo(maxs)
    segs.drawTo(maxs.x, mins.y, maxs.z)
    segs.drawTo(mins.x, mins.y, maxs.z)
    segs.drawTo(mins.x, maxs.y, maxs.z)
    segs.drawTo(maxs)
    # vertical corner edges
    segs.moveTo(mins)
    segs.drawTo(mins.x, mins.y, maxs.z)
    segs.moveTo(mins.x, maxs.y, mins.z)
    segs.drawTo(mins.x, maxs.y, maxs.z)
    segs.moveTo(maxs.x, mins.y, mins.z)
    segs.drawTo(maxs.x, mins.y, maxs.z)
    segs.moveTo(maxs.x, maxs.y, mins.z)
    segs.drawTo(maxs)
    return NodePath(segs.create())

def getLineViz(start, end, thickness, color):
    segs = LineSegs('line')
    segs.setThickness(thickness)
    segs.setColor(color)
    segs.moveTo(start)
    segs.drawTo(end)
    return NodePath(segs.create())

# All classes use the same standing/ducking collision hulls.
VEC_VIEW = Vec3(0, 0, 72)
VEC_HULL_MIN = Vec3(-24, -24, 0)
VEC_HULL_MAX = Vec3(24, 24, 82)
VEC_DUCK_HULL_MIN = Vec3(-24, -24, 0)
VEC_DUCK_HULL_MAX = Vec3(24, 24, 55)
VEC_DUCK_VIEW = Vec3(0, 0, 45)
VEC_OBS_HULL_MIN = Vec3(-10, -10, -10)
VEC_OBS_HULL_MAX = Vec3(10, 10, 10)
VEC_DEAD_VIEWHEIGHT = Vec3(0, 0, 14)

# List of models that we should preload at game launch.
# Anything that could be used during the course of the game
# that isn't tied to the map.
ModelPrecacheList = [
    "models/char/c_demo_arms",
    "models/char/c_engineer_arms",
    "models/char/c_heavy_arms",
    "models/char/c_soldier_arms",
    "models/char/c_sniper_arms",
    "models/char/c_pyro_arms",
    "models/char/demo",
    "models/char/demogib001",
    "models/char/demogib002",
    "models/char/demogib003",
    "models/char/demogib004",
    "models/char/demogib005",
    "models/char/demogib006",
    "models/char/engineer",
    "models/char/engineergib001",
    "models/char/engineergib002",
    "models/char/engineergib003",
    "models/char/engineergib004",
    "models/char/engineergib005",
    "models/char/engineergib006",
    "models/char/engineergib007",
    "models/char/heavy",
    "models/char/heavygib001",
    "models/char/heavygib002",
    "models/char/heavygib003",
    "models/char/heavygib004",
    "models/char/heavygib005",
    "models/char/heavygib006",
    "models/char/heavygib007",
    "models/char/pyro",
    "models/char/pyrogib001",
    "models/char/pyrogib002",
    "models/char/pyrogib003",
    "models/char/pyrogib004",
    "models/char/pyrogib005",
    "models/char/pyrogib006",
    "models/char/pyrogib007",
    "models/char/pyrogib008",
    "models/char/random_organ",
    "models/char/scout",
    "models/char/scoutgib001",
    "models/char/scoutgib002",
    "models/char/scoutgib003",
    "models/char/scoutgib004",
    "models/char/scoutgib005",
    "models/char/scoutgib006",
    "models/char/scoutgib007",
    "models/char/scoutgib008",
    "models/char/scoutgib009",
    "models/char/soldier",
    "models/char/soldiergib001",
    "models/char/soldiergib002",
    "models/char/soldiergib003",
    "models/char/soldiergib004",
    "models/char/soldiergib005",
    "models/char/soldiergib006",
    "models/char/soldiergib007",
    "models/char/soldiergib008",
    "models/char/spy",
    "models/char/spygib001",
    "models/char/spygib002",
    "models/char/spygib003",
    "models/char/spygib004",
    "models/char/spygib005",
    "models/char/spygib006",
    "models/char/spygib007",
    "models/char/medic",
    "models/char/medicgib001",
    "models/char/medicgib002",
    "models/char/medicgib003",
    "models/char/medicgib004",
    "models/char/medicgib005",
    "models/char/medicgib006",
    "models/char/medicgib007",
    "models/char/medicgib008",
    "models/char/sniper",
    "models/char/snipergib001",
    "models/char/snipergib002",
    "models/char/snipergib003",
    "models/char/snipergib004",
    "models/char/snipergib005",
    "models/char/snipergib006",
    "models/char/snipergib007",

    "models/buildables/sentry1",
    "models/buildables/sentry1_blueprint",
    "models/buildables/sentry1_gib1",
    "models/buildables/sentry1_gib2",
    "models/buildables/sentry1_gib3",
    "models/buildables/sentry1_gib4",
    "models/buildables/sentry2",
    "models/buildables/sentry2_heavy",
    "models/buildables/sentry2_gib1",
    "models/buildables/sentry2_gib2",
    "models/buildables/sentry2_gib3",
    "models/buildables/sentry2_gib4",
    "models/buildables/sentry3_gib1",
    "models/buildables/sentry3",
    "models/buildables/sentry3_heavy",
    "models/buildables/sentry3_rockets",
    "models/buildables/dispenser",
    "models/buildables/dispenser_light",
    "models/buildables/dispenser_blueprint",
    "models/buildables/dispenser_gib1",
    "models/buildables/dispenser_gib2",
    "models/buildables/dispenser_gib3",
    "models/buildables/dispenser_gib4",
    "models/buildables/dispenser_gib5",
    "models/buildables/teleporter",
    "models/buildables/teleporter_light",
    "models/buildables/teleporter_blueprint_enter",
    "models/buildables/teleporter_blueprint_exit",
    "models/buildables/teleporter_gib1",
    "models/buildables/teleporter_gib2",
    "models/buildables/teleporter_gib3",
    "models/buildables/teleporter_gib4",
    "models/buildables/sapper_gib001",
    "models/buildables/sapper_gib002",

    "models/effects/explosion",

    "models/weapons/c_bat",
    "models/weapons/c_bottle",
    "models/weapons/c_flamethrower",
    "models/weapons/c_flamethrower_pilotlight",
    "models/weapons/c_grenadelauncher",
    "models/weapons/c_minigun",
    "models/weapons/c_pistol",
    "models/weapons/c_rocketlauncher",
    "models/weapons/c_shotgun",
    "models/weapons/c_wrench",
    "models/weapons/c_shovel",
    "models/weapons/shell_shotgun",
    "models/weapons/v_bat_scout",
    "models/weapons/v_bottle_demoman",
    "models/weapons/v_builder_engineer",
    "models/weapons/v_fireaxe_pyro",
    "models/weapons/v_fist_heavy",
    "models/weapons/v_knife_spy",
    "models/weapons/v_pda_engineer",
    "models/weapons/v_pistol_engineer",
    "models/weapons/v_pistol_scout",
    "models/weapons/v_revolver_spy",
    "models/weapons/v_rocketlauncher_soldier",
    "models/weapons/v_scattergun_scout",
    "models/weapons/v_shotgun_engineer",
    "models/weapons/v_shotgun_heavy",
    "models/weapons/v_shotgun_pyro",
    "models/weapons/v_shotgun_soldier",
    "models/weapons/v_shovel_soldier",
    "models/weapons/v_toolbox_engineer",
    "models/weapons/v_wrench_engineer",
    "models/weapons/w_builder",
    "models/weapons/w_fireaxe",
    "models/weapons/w_grenade_grenadelauncher",
    "models/weapons/w_knife",
    "models/weapons/w_pda_engineer",
    "models/weapons/w_revolver",
    "models/weapons/w_rocket",
    "models/weapons/w_scattergun",
    "models/weapons/w_toolbox",
    "models/weapons/w_bonesaw",
    "models/weapons/v_bonesaw_medic",
    "models/weapons/v_grenadelauncher_demo",
    "models/weapons/v_minigun_heavy",
    "models/weapons/w_sniperrifle",
    "models/weapons/v_sniperrifle_sniper",
    "models/weapons/w_smg",
    "models/weapons/v_smg_sniper",
    "models/weapons/c_machete",
    "models/weapons/w_stickybomb_launcher",
    "models/weapons/v_stickybomb_launcher_demo",
    "models/weapons/w_stickybomb",
    "models/weapons/w_stickybomb_gib1",
    "models/weapons/w_stickybomb_gib2",
    "models/weapons/w_stickybomb_gib3",
    "models/weapons/w_stickybomb_gib4",
    "models/weapons/w_stickybomb_gib5",
    "models/weapons/w_stickybomb_gib6"
]

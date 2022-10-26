
from panda3d.core import *

from tf.actor.Activity import Activity
from tf.tfbase import TFLocalizer

class VoiceCommand:
    Medic = 0
    Help = 1
    Thanks = 2
    BattleCry = 3
    Incoming = 4
    GoodJob = 5
    NiceShot = 6
    Cheers = 7
    Positive = 8
    Jeers = 9
    Negative = 10
    SentryHere = 11
    TeleporterHere = 12
    DispenserHere = 13
    SentryAhead = 14
    ChargeReady = 15
    ActivateCharge = 16
    Yes = 17
    No = 18
    Go = 19
    MoveUp = 20
    GoLeft = 21
    GoRight = 22
    Spy = 23


class Class:
    Invalid   = -1
    Scout     = 0
    Soldier   = 1
    Pyro      = 2
    Demo      = 3
    HWGuy     = 4
    Engineer  = 5
    Medic     = 6
    Sniper    = 7
    Spy       = 8

    COUNT = 9

class Weapon:
    PistolEngineer = 0
    PistolScout = 1
    Wrench = 2
    ConstructionPDA = 3
    DestructionPDA = 4
    Shovel = 5
    Bottle = 6
    RocketLauncher = 7
    Minigun = 8
    GrenadeLauncher = 9
    Scattergun = 10
    ShotgunEngineer = 11
    ShotgunSoldier = 12
    ShotgunHeavy = 13
    ShotgunPyro = 14
    Bat = 15
    Fists = 16
    FireAxe = 17
    Revolver = 18
    Knife = 19
    Toolbox = 20
    BoneSaw = 21
    MediGun = 22
    SyringeGun = 23
    SniperRifle = 24
    SMG = 25
    Machete = 26
    StickyBombLauncher = 27
    FlameThrower = 28

BaseSpeed = 300

class EngineerInfo:
    Name = TFLocalizer.Engineer
    MenuWeapon = "models/weapons/c_wrench"
    PlayerModel = "models/char/engineer"
    ViewModel = "models/char/c_engineer_arms"
    ForwardFactor = 1.0
    BackwardFactor = 0.9
    CrouchFactor = 0.33
    SwimmingFactor = 0.8
    ViewHeight = 68
    MaxHealth = 125
    Phonemes = 'engineer'
    DontDoAirWalk = False
    Expressions = {
        'idle': ['defaultFace'],
        'specialAction': ['specialAction01'],
        'pain': ['painSmall']
    }

    HeadRotationOffset = Vec3(0, -80, 0)

    PainFilenames = [
        "Engineer.PainSevere01",
        "Engineer.PainSevere02",
        "Engineer.PainSevere03",
        "Engineer.PainSevere04",
        "Engineer.PainSevere05",
        "Engineer.PainSevere06",
        "Engineer.PainSevere07"
    ]

    CritPainFilenames = [
        "Engineer.PainCrticialDeath01",
        "Engineer.PainCrticialDeath02",
        "Engineer.PainCrticialDeath03",
        "Engineer.PainCrticialDeath04",
        "Engineer.PainCrticialDeath05",
        "Engineer.PainCrticialDeath06"
    ]

    SharpPainFilenames = [
        "Engineer.PainSharp01",
        "Engineer.PainSharp02",
        "Engineer.PainSharp03",
        "Engineer.PainSharp04",
        "Engineer.PainSharp05",
        "Engineer.PainSharp06",
        "Engineer.PainSharp07",
        "Engineer.PainSharp08"
    ]

    TeleporterThanks = [
        "Engineer.ThanksForTheTeleporter01",
        "Engineer.ThanksForTheTeleporter02"
    ]

    ThanksForHeal = [
        "Engineer.ThanksForTheHeal01",
        "Engineer.ThanksForTheHeal02"
    ]

    VoiceCommands = {
        VoiceCommand.Medic: [
            "Engineer.Medic01",
            "Engineer.Medic02",
            "Engineer.Medic03"
        ]
    }

    Weapons = [Weapon.ShotgunEngineer, Weapon.PistolEngineer, Weapon.Wrench, Weapon.ConstructionPDA, Weapon.DestructionPDA, Weapon.Toolbox]

class SoldierInfo:
    Name = TFLocalizer.Soldier
    MenuWeapon = "models/weapons/c_rocketlauncher"
    PlayerModel = "models/char/soldier"
    ViewModel = "models/char/c_soldier_arms"
    ForwardFactor = 0.8
    BackwardFactor = 0.72
    CrouchFactor = 0.27
    SwimmingFactor = 0.64
    ViewHeight = 68
    MaxHealth = 200
    Phonemes = 'soldier'
    DontDoAirWalk = True

    Expressions = {
        'idle': [],
        'specialAction': ['specialAction01'],
        'pain': ['painSmall']
    }

    HeadRotationOffset = Vec3(0, -80, 0)

    PainFilenames = [
        "Soldier.PainSevere01",
        "Soldier.PainSevere02",
        "Soldier.PainSevere03",
        "Soldier.PainSevere04",
        "Soldier.PainSevere05",
        "Soldier.PainSevere06"
    ]

    CritPainFilenames = [
        "Soldier.PainCrticialDeath01",
        "Soldier.PainCrticialDeath02",
        "Soldier.PainCrticialDeath03",
        "Soldier.PainCrticialDeath04"
    ]

    SharpPainFilenames = [
        "Soldier.PainSharp01",
        "Soldier.PainSharp02",
        "Soldier.PainSharp03",
        "Soldier.PainSharp04",
        "Soldier.PainSharp05",
        "Soldier.PainSharp06",
        "Soldier.PainSharp07",
        "Soldier.PainSharp08"
    ]

    TeleporterThanks = [
        "Soldier.ThanksForTheTeleporter01",
        "Soldier.ThanksForTheTeleporter02",
        "Soldier.ThanksForTheTeleporter03"
    ]

    ThanksForHeal = [
        "Soldier.ThanksForTheHeal01",
        "Soldier.ThanksForTheHeal02",
        "Soldier.ThanksForTheHeal03"
    ]

    VoiceCommands = {
        VoiceCommand.Medic: [
            "Soldier.Medic01",
            "Soldier.Medic02",
            "Soldier.Medic03"
        ]
    }

    Weapons = [Weapon.RocketLauncher,
               Weapon.ShotgunSoldier,
               Weapon.Shovel]

class DemoInfo:
    Name = TFLocalizer.Demoman
    MenuWeapon = "models/weapons/c_grenadelauncher"
    PlayerModel = "models/char/demo"
    ViewModel = "models/char/c_demo_arms"
    ForwardFactor = 0.93
    BackwardFactor = 0.84
    CrouchFactor = 0.31
    SwimmingFactor = 0.75
    ViewHeight = 68
    MaxHealth = 175
    Phonemes = 'demo'
    DontDoAirWalk = False

    Expressions = {
        'idle': ['defaultFace'],
        'specialAction': ['evilHappy'],
        'pain': ['pain']
    }

    HeadRotationOffset = Vec3(0, -80, 0)

    PainFilenames = [
        "Demoman.PainSevere01",
        "Demoman.PainSevere02",
        "Demoman.PainSevere03",
        "Demoman.PainSevere04"
    ]

    CritPainFilenames = [
        "Demoman.PainCrticialDeath01",
        "Demoman.PainCrticialDeath02",
        "Demoman.PainCrticialDeath03",
        "Demoman.PainCrticialDeath04",
        "Demoman.PainCrticialDeath05"
    ]

    SharpPainFilenames = [
        "Demoman.PainSharp01",
        "Demoman.PainSharp02",
        "Demoman.PainSharp03",
        "Demoman.PainSharp04",
        "Demoman.PainSharp05",
        "Demoman.PainSharp06",
        "Demoman.PainSharp07"
    ]

    TeleporterThanks = [
        "Demoman.ThanksForTheTeleporter01",
        "Demoman.ThanksForTheTeleporter02"
    ]

    ThanksForHeal = [
        "Demoman.ThanksForTheHeal01",
        "Demoman.ThanksForTheHeal02",
        "Demoman.ThanksForTheHeal03"
    ]

    VoiceCommands = {
        VoiceCommand.Medic: [
            "Demoman.Medic01",
            "Demoman.Medic02",
            "Demoman.Medic03"
        ]
    }

    Weapons = [Weapon.GrenadeLauncher, Weapon.StickyBombLauncher, Weapon.Bottle]

class HeavyInfo:
    Name = TFLocalizer.Heavy
    MenuWeapon = "models/weapons/c_minigun"
    PlayerModel = "models/char/heavy"
    ViewModel = "models/char/c_heavy_arms"
    ForwardFactor = 0.77
    BackwardFactor = 0.69
    CrouchFactor = 0.26
    SwimmingFactor = 0.61
    ViewHeight = 75
    MaxHealth = 300
    Phonemes = 'heavy'
    DontDoAirWalk = False
    Expressions = {
        'idle': ['idleface'],
        'specialAction': ['actionfire01'],
        'pain': ['upset1']
    }

    HeadRotationOffset = Vec3(40, -80, 0)

    PainFilenames = [
        "Heavy.PainSevere01",
        "Heavy.PainSevere02",
        "Heavy.PainSevere03"
    ]

    CritPainFilenames = [
        "Heavy.PainCrticialDeath01",
        "Heavy.PainCrticialDeath02",
        "Heavy.PainCrticialDeath03"
    ]

    SharpPainFilenames = [
        "Heavy.PainSharp01",
        "Heavy.PainSharp02",
        "Heavy.PainSharp03",
        "Heavy.PainSharp04",
        "Heavy.PainSharp05"
    ]

    TeleporterThanks = [
        "Heavy.ThanksForTheTeleporter01",
        "Heavy.ThanksForTheTeleporter02",
        "Heavy.ThanksForTheTeleporter03"
    ]

    ThanksForHeal = [
        "Heavy.ThanksForTheHeal01",
        "Heavy.ThanksForTheHeal02",
        "Heavy.ThanksForTheHeal03"
    ]

    VoiceCommands = {
        VoiceCommand.Medic: [
            "Heavy.Medic01",
            "Heavy.Medic02",
            "Heavy.Medic03"
        ]
    }

    Weapons = [Weapon.Minigun, Weapon.ShotgunHeavy, Weapon.Fists]

class ScoutInfo:
    Name = TFLocalizer.Scout
    MenuWeapon = "models/weapons/w_scattergun"
    PlayerModel = "models/char/scout"
    ViewModel = "models/weapons/v_scattergun_scout"
    ForwardFactor = 1.33
    BackwardFactor = 1.2
    CrouchFactor = 0.44
    SwimmingFactor = 1.07
    ViewHeight = 65
    MaxHealth = 125
    Phonemes = 'scout'
    DontDoAirWalk = True
    Expressions = {
        'idle': [],
        'specialAction': ['specialAction01'],
        'pain': ['painSmall']
    }

    HeadRotationOffset = Vec3(40, -80, 0)

    PainFilenames = [
        "Scout.PainSevere01",
        "Scout.PainSevere02",
        "Scout.PainSevere03",
        "Scout.PainSevere04",
        "Scout.PainSevere05",
        "Scout.PainSevere06"
    ]
    CritPainFilenames = [
        "Scout.PainCrticialDeath01",
        "Scout.PainCrticialDeath02",
        "Scout.PainCrticialDeath03"
    ]
    SharpPainFilenames = [
        "Scout.PainSharp01",
        "Scout.PainSharp02",
        "Scout.PainSharp03",
        "Scout.PainSharp04",
        "Scout.PainSharp05",
        "Scout.PainSharp06",
        "Scout.PainSharp07",
        "Scout.PainSharp08"
    ]
    TeleporterThanks = [
        "Scout.ThanksForTheTeleporter01",
        "Scout.ThanksForTheTeleporter02",
        "Scout.ThanksForTheTeleporter03"
    ]
    ThanksForHeal = [
        "Scout.ThanksForTheHeal01",
        "Scout.ThanksForTheHeal02",
        "Scout.ThanksForTheHeal03"
    ]
    VoiceCommands = {
        VoiceCommand.Medic: [
            "Scout.Medic01",
            "Scout.Medic02",
            "Scout.Medic03"
        ]
    }

    Weapons = [Weapon.Scattergun, Weapon.PistolScout, Weapon.Bat]

class PyroInfo:
    Name = TFLocalizer.Pyro
    MenuWeapon = ["models/weapons/c_flamethrower", "models/weapons/c_flamethrower_pilotlight"]
    PlayerModel = "models/char/pyro"
    ViewModel = "models/char/c_pyro_arms"
    ForwardFactor = 1.0
    BackwardFactor = 0.9
    CrouchFactor = 0.33
    SwimmingFactor = 0.8
    ViewHeight = 68
    MaxHealth = 175
    Phonemes = None
    Expressions = None
    DontDoAirWalk = True

    HeadRotationOffset = Vec3(40, -80, 0)

    PainFilenames = [
        "Pyro.PainSevere01",
        "Pyro.PainSevere02",
        "Pyro.PainSevere03",
        "Pyro.PainSevere04",
        "Pyro.PainSevere05",
        "Pyro.PainSevere06"
    ]
    CritPainFilenames = [
        "Pyro.PainCrticialDeath01",
        "Pyro.PainCrticialDeath02",
        "Pyro.PainCrticialDeath03"
    ]
    SharpPainFilenames = [
        "Pyro.PainSharp01",
        "Pyro.PainSharp02",
        "Pyro.PainSharp03",
        "Pyro.PainSharp04",
        "Pyro.PainSharp05",
        "Pyro.PainSharp06",
        "Pyro.PainSharp07"
    ]
    TeleporterThanks = [
        "Pyro.ThanksForTheTeleporter01"
    ]
    ThanksForHeal = [
        "Pyro.ThanksForTheHeal01"
    ]
    VoiceCommands = {
        VoiceCommand.Medic: [
            "Pyro.Medic01"
        ]
    }

    Weapons = [Weapon.FlameThrower, Weapon.ShotgunPyro, Weapon.FireAxe]

class SpyInfo:
    Name = TFLocalizer.Spy
    MenuWeapon = "models/weapons/w_knife"
    PlayerModel = "models/char/spy"
    ViewModel = "models/weapons/v_revolver_spy"
    ForwardFactor = 1.07
    BackwardFactor = 0.96
    CrouchFactor = 0.36
    SwimmingFactor = 0.85
    ViewHeight = 75
    MaxHealth = 125
    Phonemes = 'spy'
    DontDoAirWalk = True
    Expressions = {
        'idle': ['defaultFace'],
        'specialAction': ['specialAction01'],
        'pain': ['painSmall']
    }

    HeadRotationOffset = Vec3(0, -80, 0)

    PainFilenames = [
        "Spy.PainSevere01",
        "Spy.PainSevere02",
        "Spy.PainSevere03",
        "Spy.PainSevere04",
        "Spy.PainSevere05"
    ]
    CritPainFilenames = [
        "Spy.PainCrticialDeath01",
        "Spy.PainCrticialDeath02",
        "Spy.PainCrticialDeath03"
    ]
    SharpPainFilenames = [
        "Spy.PainSharp01",
        "Spy.PainSharp02",
        "Spy.PainSharp03",
        "Spy.PainSharp04"
    ]
    TeleporterThanks = [
        "Spy.ThanksForTheTeleporter01",
        "Spy.ThanksForTheTeleporter02",
        "Spy.ThanksForTheTeleporter03"
    ]
    ThanksForHeal = [
        "Spy.ThanksForTheHeal01",
        "Spy.ThanksForTheHeal02",
        "Spy.ThanksForTheHeal03"
    ]
    VoiceCommands = {
        VoiceCommand.Medic: [
            "Spy.Medic01",
            "Spy.Medic02",
            "Spy.Medic03"
        ]
    }

    Weapons = [Weapon.Revolver, Weapon.Knife]


class MedicInfo:
    Name = TFLocalizer.Medic
    MenuWeapon = "models/weapons/w_medigun"
    PlayerModel = "models/char/medic"
    ViewModel = "models/weapons/v_bonesaw_medic"
    ForwardFactor = 1.07
    BackwardFactor = 0.96
    CrouchFactor = 0.36
    SwimmingFactor = 0.85
    ViewHeight = 75
    MaxHealth = 150
    Phonemes = 'medic'
    DontDoAirWalk = False
    Expressions = {
        'idle': ['defaultFace'],
        'specialAction': ['specialAction01'],
        'pain': ['painSmall']
    }

    HeadRotationOffset = Vec3(0, -80, 0)

    PainFilenames = [
        "Medic.PainSevere01",
        "Medic.PainSevere02",
        "Medic.PainSevere03",
        "Medic.PainSevere04"
    ]
    CritPainFilenames = [
        "Medic.PainCrticialDeath01",
        "Medic.PainCrticialDeath02",
        "Medic.PainCrticialDeath03",
        "Medic.PainCrticialDeath04"
    ]
    SharpPainFilenames = [
        "Medic.PainSharp01",
        "Medic.PainSharp02",
        "Medic.PainSharp03",
        "Medic.PainSharp04",
        "Medic.PainSharp05",
        "Medic.PainSharp06",
        "Medic.PainSharp07",
        "Medic.PainSharp08"
    ]
    TeleporterThanks = [
        "Medic.ThanksForTheTeleporter01",
        "Medic.ThanksForTheTeleporter02",
        "Medic.ThanksForTheTeleporter03"
    ]
    ThanksForHeal = [
        "Medic.ThanksForTheHeal01",
        "Medic.ThanksForTheHeal02"
    ]
    VoiceCommands = {
        VoiceCommand.Medic: [
            "Medic.Medic01",
            "Medic.Medic02",
            "Medic.Medic03"
        ]
    }

    Weapons = [Weapon.MediGun, Weapon.BoneSaw]

class SniperInfo:
    Name = TFLocalizer.Sniper
    MenuWeapon = "models/weapons/w_sniperrifle"
    PlayerModel = "models/char/sniper"
    ViewModel = "models/char/c_sniper_arms"
    ForwardFactor = 1.0
    BackwardFactor = 0.9
    CrouchFactor = 0.33
    SwimmingFactor = 0.8
    ViewHeight = 75
    MaxHealth = 125
    Phonemes = 'sniper'
    DontDoAirWalk = True
    Expressions = {
        'idle': ['defaultFace'],
        'specialAction': ['specialAction01'],
        'pain': ['painSmall']
    }

    HeadRotationOffset = Vec3(0, -80, 0)

    PainFilenames = [
        "Sniper.PainSevere01",
        "Sniper.PainSevere02",
        "Sniper.PainSevere03",
        "Sniper.PainSevere04"
    ]
    CritPainFilenames = [
        "Sniper.PainCrticialDeath01",
        "Sniper.PainCrticialDeath02",
        "Sniper.PainCrticialDeath03",
        "Sniper.PainCrticialDeath04"
    ]
    SharpPainFilenames = [
        "Sniper.PainSharp01",
        "Sniper.PainSharp02",
        "Sniper.PainSharp03",
        "Sniper.PainSharp04"
    ]
    TeleporterThanks = [
        "Sniper.ThanksForTheTeleporter01",
        "Sniper.ThanksForTheTeleporter02",
        "Sniper.ThanksForTheTeleporter03"
    ]
    ThanksForHeal = [
        "Sniper.ThanksForTheHeal01",
        "Sniper.ThanksForTheHeal02",
        "Sniper.ThanksForTheHeal03"
    ]
    VoiceCommands = {
        VoiceCommand.Medic: [
            "Sniper.Medic01",
            "Sniper.Medic02"
        ]
    }

    Weapons = [Weapon.SniperRifle, Weapon.SMG, Weapon.Machete]

ClassInfos = {
    Class.Soldier: SoldierInfo,
    Class.Demo: DemoInfo,
    Class.Engineer: EngineerInfo,
    Class.HWGuy: HeavyInfo,
    Class.Scout: ScoutInfo,
    Class.Pyro: PyroInfo,
    Class.Spy: SpyInfo,
    Class.Medic: MedicInfo,
    Class.Sniper: SniperInfo
}

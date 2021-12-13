
from enum import IntEnum, auto

from panda3d.core import *

from tf.actor.Activity import Activity
from tf.tfbase import TFLocalizer

class Class(IntEnum):
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

class Weapon(IntEnum):
    Shotgun = 0
    Pistol = auto()
    Wrench = auto()
    ConstructionPDA = auto()
    DestructionPDA = auto()
    ShotgunSecondary = auto()
    Shovel = auto()
    Bottle = auto()
    RocketLauncher = auto()
    Minigun = auto()
    GrenadeLauncher = auto()

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

    Weapons = [Weapon.Shotgun, Weapon.Pistol, Weapon.Wrench]

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

    Weapons = [Weapon.RocketLauncher,
               Weapon.ShotgunSecondary,
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

    Weapons = [Weapon.GrenadeLauncher, Weapon.Bottle]

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

    Weapons = [Weapon.Minigun, Weapon.ShotgunSecondary]

ClassInfos = {
    Class.Soldier: SoldierInfo,
    Class.Demo: DemoInfo,
    Class.Engineer: EngineerInfo,
    Class.HWGuy: HeavyInfo
}

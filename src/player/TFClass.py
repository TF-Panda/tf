
from enum import IntEnum, auto

from panda3d.core import *

from tf.character.Activity import Activity

class Class(IntEnum):
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

BaseSpeed = 300

class EngineerInfo:
    PlayerModel = "tfmodels/src/char/engineer/engineer.pmdl"
    ViewModel = "tfmodels/src/char/engineer/engineer_viewmodel/c_engineer_arms.pmdl"
    ForwardFactor = 1.0
    BackwardFactor = 0.9
    CrouchFactor = 0.33
    ViewHeight = 68
    MaxHealth = 125
    BBox = [Point3(-9.058, -27.026, -4.007),
            Point3(11.751, 25.998, 80.894)]

    Weapons = [Weapon.Shotgun]

ClassInfos = {
    Class.Engineer: EngineerInfo
}

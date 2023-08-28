"""DistributedFireAxe module: contains the DistributedFireAxe class."""

from tf.tfbase import TFLocalizer

from .TFWeaponMelee import TFWeaponMelee
from .WeaponMode import TFWeaponMode, TFWeaponType


class DistributedFireAxe(TFWeaponMelee):

    WeaponModel = "models/weapons/w_fireaxe"
    WeaponViewModel = "models/weapons/v_fireaxe_pyro"
    UsesViewModel = True
    MinViewModelOffset = (10, 0, -9)

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary]['damage'] = 65
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['smackDelay'] = 0.2

    def getSingleSound(self):
        return "Weapon_FireAxe.Miss"

    def getHitPlayerSound(self):
        return "Weapon_FireAxe.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_FireAxe.HitWorld"

    def getName(self):
        return TFLocalizer.FireAxe

if not IS_CLIENT:
    DistributedFireAxeAI = DistributedFireAxe
    DistributedFireAxeAI.__name__ = 'DistributedFireAxeAI'

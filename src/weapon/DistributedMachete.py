"""DistributedMachete module: contains the DistributedMachete class."""

from .TFWeaponMelee import TFWeaponMelee
from .WeaponMode import TFWeaponType, TFWeaponMode

from tf.tfbase import TFLocalizer

class DistributedMachete(TFWeaponMelee):
    WeaponModel = "models/weapons/c_machete"
    WeaponViewModel = "models/weapons/c_machete"
    UsesViewModel = False

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary]['damage'] = 65
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['smackDelay'] = 0.2

    def getSingleSound(self):
        return "Weapon_Machete.Miss"

    def getHitPlayerSound(self):
        return "Weapon_Machete.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Machete.HitWorld"

    def getName(self):
        return TFLocalizer.Kukri

if not IS_CLIENT:
    DistributedMacheteAI = DistributedMachete
    DistributedMacheteAI.__name__ = 'DistributedMacheteAI'

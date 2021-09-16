from .TFWeaponMelee import TFWeaponMelee

from .WeaponMode import TFWeaponType, TFWeaponMode

from tf.tfbase import TFLocalizer

class DShovel(TFWeaponMelee):

    WeaponModel = "models/weapons/c_shovel"
    WeaponViewModel = "models/weapons/c_shovel"

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary]['damage'] = 65
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['smackDelay'] = 0.2

    def getSingleSound(self):
        return "Weapon_Shovel.Miss"

    def getHitPlayerSound(self):
        return "Weapon_Shovel.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Shovel.HitWorld"

    def getName(self):
        return TFLocalizer.Shovel

if not IS_CLIENT:
    DShovelAI = DShovel
    DShovelAI.__name__ = 'DShovelAI'

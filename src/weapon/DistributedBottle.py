from .TFWeaponMelee import TFWeaponMelee

from .WeaponMode import TFWeaponType, TFWeaponMode

from tf.tfbase import TFLocalizer

class DistributedBottle(TFWeaponMelee):

    WeaponModel = "models/weapons/c_bottle"
    WeaponViewModel = "models/weapons/v_bottle_demoman"
    UsesViewModel = True

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary]['damage'] = 65
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['smackDelay'] = 0.2

    def getSingleSound(self):
        return "Weapon_Bottle.Miss"

    def getHitPlayerSound(self):
        return "Weapon_Bottle.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Bottle.HitWorld"

    def getName(self):
        return TFLocalizer.Bottle

if not IS_CLIENT:
    DistributedBottleAI = DistributedBottle
    DistributedBottleAI.__name__ = 'DistributedBottleAI'

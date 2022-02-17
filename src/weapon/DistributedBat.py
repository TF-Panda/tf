from .TFWeaponMelee import TFWeaponMelee

from .WeaponMode import TFWeaponMode, TFWeaponType

from tf.tfbase import TFLocalizer

class DistributedBat(TFWeaponMelee):
    WeaponModel = "models/weapons/c_bat"
    WeaponViewModel = "models/weapons/v_bat_scout"
    UsesViewModel = True

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary].update({
          'damage': 35,
          'timeFireDelay': 0.5,
          'smackDelay': 0.2,
          'timeIdle': 5.0
        })

    def getSingleSound(self):
        return "Weapon_Bat.Miss"

    def getHitPlayerSound(self):
        return "Weapon_Bat.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Bat.HitWorld"

    def getName(self):
        return TFLocalizer.Bat

if not IS_CLIENT:
    DistributedBatAI = DistributedBat
    DistributedBatAI.__name__ = 'DistributedBatAI'

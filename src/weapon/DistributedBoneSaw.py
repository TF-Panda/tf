"""DistributedBoneSaw module: contains the DistributedBoneSaw class."""

from tf.tfbase import TFLocalizer

from .TFWeaponMelee import TFWeaponMelee
from .WeaponMode import TFWeaponMode, TFWeaponType


class DistributedBoneSaw(TFWeaponMelee):
    WeaponModel = "models/weapons/w_bonesaw"
    WeaponViewModel = "models/weapons/v_bonesaw_medic"
    UsesViewModel = True

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary].update({
          'damage': 65,
          'timeFireDelay': 0.8,
          'smackDelay': 0.2
        })

    def getSingleSound(self):
        return "Weapon_BoneSaw.Miss"

    def getHitPlayerSound(self):
        return "Weapon_BoneSaw.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_BoneSaw.HitWorld"

    def getName(self):
        return TFLocalizer.BoneSaw

if not IS_CLIENT:
    DistributedBoneSawAI = DistributedBoneSaw
    DistributedBoneSawAI.__name__ = 'DistributedBoneSawAI'

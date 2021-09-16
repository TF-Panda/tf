
from .TFWeaponGun import TFWeaponGun

from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponMode, TFWeaponType
from tf.tfbase.TFGlobals import DamageType

class DPistol(TFWeaponGun):

    WeaponModel = "models/weapons/c_pistol"
    WeaponViewModel = "models/weapons/c_pistol"

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = False
        self.maxAmmo = 200
        self.maxClip = 12
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.primaryAttackInterval = 0.15
        self.weaponType = TFWeaponType.Secondary
        self.weaponData[TFWeaponMode.Primary]['spread'] = 0.07
        self.weaponData[TFWeaponMode.Primary]['damage'] = 12
        self.damageType = DamageType.Bullet | DamageType.UseDistanceMod

    def getName(self):
        return TFLocalizer.Pistol

    def getSingleSound(self):
        return "Weapon_Pistol.Single"

    def getEmptySound(self):
        return "Weapon_Pistol.Empty"

if not IS_CLIENT:
    DPistolAI = DPistol
    DPistolAI.__name__ = 'DPistolAI'

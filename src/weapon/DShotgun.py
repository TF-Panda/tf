
from .TFWeaponGun import TFWeaponGun

from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponMode
from tf.tfbase.TFGlobals import DamageType

class DShotgun(TFWeaponGun):

    WeaponModel = "models/weapons/c_shotgun"
    WeaponViewModel = "models/weapons/c_shotgun"

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = True
        self.maxAmmo = 32
        self.maxClip = 6
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.primaryAttackInterval = 0.625
        self.weaponData[TFWeaponMode.Primary]['bulletsPerShot'] = 10
        self.weaponData[TFWeaponMode.Primary]['spread'] = 0.0675
        self.weaponData[TFWeaponMode.Primary]['damage'] = 6
        self.weaponData[TFWeaponMode.Primary]['range'] = 8192
        self.weaponData[TFWeaponMode.Primary]['punchAngle'] = 3.0
        self.weaponData[TFWeaponMode.Primary]['timeIdle'] = 5.0
        self.weaponData[TFWeaponMode.Primary]['timeIdleEmpty'] = 0.25
        self.weaponData[TFWeaponMode.Primary]['timeReloadStart'] = 0.1
        self.weaponData[TFWeaponMode.Primary]['timeReload'] = 0.5
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.625
        self.damageType = DamageType.Buckshot | DamageType.UseDistanceMod

    def getName(self):
        return TFLocalizer.Shotgun

    def getSingleSound(self):
        return "Weapon_Shotgun.Single"

    def getEmptySound(self):
        return "Weapon_Shotgun.Empty"

if not IS_CLIENT:
    DShotgunAI = DShotgun
    DShotgunAI.__name__ = 'DShotgunAI'

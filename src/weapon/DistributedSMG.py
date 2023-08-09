"""DistributedSMG module: contains the DistributedSMG class."""

from tf.tfbase import TFLocalizer
from tf.tfbase.TFGlobals import DamageType

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFWeaponMode, TFWeaponType


class DistributedSMG(TFWeaponGun):
    WeaponModel = "models/weapons/w_smg"
    WeaponViewModel = "models/weapons/v_smg_sniper"
    UsesViewModel = True

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.weaponType = TFWeaponType.Secondary
        self.weaponData[TFWeaponMode.Primary].update({
          'damage': 8,
          'range': 8192,
          'bulletsPerShot': 1,
          'spread': 0.025,
          'timeIdle': 10.0,
          'timeIdleEmpty': 1.0,
          'timeFireDelay': 0.1
        })
        self.primaryAttackInterval = 0.1
        self.reloadsSingly = False
        self.usesAmmo = True
        self.usesClip = True
        self.usesAmmo2 = False
        self.usesClip2 = False

        self.maxAmmo = 75
        self.ammo = self.maxAmmo
        self.maxClip = 25
        self.clip = self.maxClip
        self.damageType = DamageType.Bullet | DamageType.UseDistanceMod

    def getName(self):
        return TFLocalizer.SMG

    def getSingleSound(self):
        return "Weapon_SMG.Single"

    def getEmptySound(self):
        return "Weapon_SMG.ClipEmpty"

    def getReloadSound(self):
        return "Weapon_SMG.WorldReload"

if not IS_CLIENT:
    DistributedSMGAI = DistributedSMG
    DistributedSMGAI.__name__ = 'DistributedSMGAI'

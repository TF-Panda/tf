"""DistributedGrenadeLauncher module: contains the DistributedGrenadeLauncher class."""

from tf.tfbase import TFLocalizer
from tf.tfbase.TFGlobals import DamageType

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFProjectileType, TFWeaponMode


class DistributedGrenadeLauncher(TFWeaponGun):
    WeaponModel = "models/weapons/c_grenadelauncher"
    WeaponViewModel = "models/weapons/v_grenadelauncher_demo"
    UsesViewModel = True
    MinViewModelOffset = (10, 0, -10)

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.reloadsSingly = True
        self.usesClip = True
        self.usesAmmo = True
        self.maxAmmo = 16
        self.maxClip = 4
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.primaryAttackInterval = 0.6
        self.weaponData[TFWeaponMode.Primary]['damage'] = 100
        self.weaponData[TFWeaponMode.Primary]['projectile'] = TFProjectileType.Pipebomb
        self.weaponData[TFWeaponMode.Primary]['punchAngle'] = 3.0
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.6
        self.weaponData[TFWeaponMode.Primary]['timeIdle'] = 0.6
        self.weaponData[TFWeaponMode.Primary]['timeIdleEmpty'] = 0.6
        self.weaponData[TFWeaponMode.Primary]['timeReloadStart'] = 0.1
        self.weaponData[TFWeaponMode.Primary]['timeReload'] = 0.6
        self.damageType = DamageType.Blast | DamageType.HalfFalloff

    def getName(self):
        return TFLocalizer.GrenadeLauncher

    def getSingleSound(self):
        return "Weapon_GrenadeLauncher.Single"

    def getReloadSound(self):
        return "Weapon_GrenadeLauncher.WorldReload"

if not IS_CLIENT:
    DistributedGrenadeLauncherAI = DistributedGrenadeLauncher
    DistributedGrenadeLauncherAI.__name__ = 'DistributedGrenadeLauncherAI'

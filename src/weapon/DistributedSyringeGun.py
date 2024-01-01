"""DistributedSyringeGun module: contains the DistributedSyringeGun class."""

from tf.tfbase import TFLocalizer
from tf.tfbase.TFGlobals import DamageType

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFWeaponMode, TFWeaponType, TFProjectileType

class DistributedSyringeGun(TFWeaponGun):

    WeaponModel = "models/weapons/w_syringegun"
    WeaponViewModel = "models/weapons/v_syringegun_medic"
    UsesViewModel = True
    #MinViewModelOffset = (0, 0, 0)

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = False
        self.maxClip = 40
        self.maxAmmo = 150
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.weaponType = TFWeaponType.Primary
        self.primaryAttackInterval = 0.1
        self.weaponData[TFWeaponMode.Primary]['spread'] = 0.0
        self.weaponData[TFWeaponMode.Primary]['range'] = 8192
        self.weaponData[TFWeaponMode.Primary]['damage'] = 10
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.1
        self.weaponData[TFWeaponMode.Primary]['timeIdle'] = 5.0
        self.weaponData[TFWeaponMode.Primary]['timeIdleEmpty'] = 0.25
        self.weaponData[TFWeaponMode.Primary]['projectile'] = TFProjectileType.Syringe
        self.damageType = DamageType.Bullet | DamageType.UseDistanceMod | DamageType.NoCloseDistanceMod | DamageType.PreventPhysicsForce

    def getName(self):
        return TFLocalizer.SyringeGun

    def getSingleSound(self):
        return "Weapon_SyringeGun.Single"

    def getEmptySound(self):
        return "Weapon_SyringeGun.ClipEmpty"

    def getReloadSound(self):
        return "Weapon_SyringeGun.WorldReload"

if not IS_CLIENT:
    DistributedSyringeGunAI = DistributedSyringeGun
    DistributedSyringeGunAI.__name__ = 'DistributedSyringeGunAI'

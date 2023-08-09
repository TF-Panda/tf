"""DistributedRevolver module: contains the DistributedRevolver class."""

from tf.tfbase import TFLocalizer
from tf.tfbase.TFGlobals import DamageType

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFWeaponMode, TFWeaponType


class DistributedRevolver(TFWeaponGun):

    WeaponModel = "models/weapons/w_revolver"
    WeaponViewModel = "models/weapons/v_revolver_spy"
    UsesViewModel = True

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = False
        self.maxClip = 6
        self.maxAmmo = 24
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.primaryAttackInterval = 0.5
        self.weaponType = TFWeaponType.Secondary
        self.weaponData[TFWeaponMode.Primary]['spread'] = 0.025
        self.weaponData[TFWeaponMode.Primary]['range'] = 4096
        self.weaponData[TFWeaponMode.Primary]['damage'] = 40
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.5
        self.damageType = DamageType.Bullet | DamageType.UseDistanceMod

    def getName(self):
        return TFLocalizer.Revolver

    def getSingleSound(self):
        return "Weapon_Revolver.Single"

    def getEmptySound(self):
        return "Weapon_Revolver.ClipEmpty"

    def getReloadSound(self):
        return "Weapon_Revolver.WorldReload"

if not IS_CLIENT:
    DistributedRevolverAI = DistributedRevolver
    DistributedRevolverAI.__name__ = 'DistributedRevolverAI'

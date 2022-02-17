
from .TFWeaponGun import TFWeaponGun

from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponMode, TFWeaponType
from tf.tfbase.TFGlobals import DamageType

class DistributedPistol(TFWeaponGun):

    WeaponModel = "models/weapons/c_pistol"
    UsesViewModel = True

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = False
        self.maxClip = 12
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.primaryAttackInterval = 0.15
        self.weaponType = TFWeaponType.Secondary
        self.weaponData[TFWeaponMode.Primary]['spread'] = 0.04
        self.weaponData[TFWeaponMode.Primary]['range'] = 4096
        self.weaponData[TFWeaponMode.Primary]['damage'] = 15
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.15
        self.weaponData[TFWeaponMode.Primary]['timeIdle'] = 5.0
        self.weaponData[TFWeaponMode.Primary]['timeIdleEmpty'] = 0.25
        self.weaponData[TFWeaponMode.Primary]['timeReload'] = 0.5
        self.damageType = DamageType.Bullet | DamageType.UseDistanceMod

    def getName(self):
        return TFLocalizer.Pistol

    def getSingleSound(self):
        return "Weapon_Pistol.Single"

    def getEmptySound(self):
        return "Weapon_Pistol.Empty"

    def getReloadSound(self):
        return "Weapon_Pistol.WorldReload"

class DistributedPistolEngineer(DistributedPistol):
    WeaponViewModel = "models/weapons/v_pistol_engineer"

    def __init__(self):
        DistributedPistol.__init__(self)
        self.maxAmmo = 200
        self.ammo = self.maxAmmo

class DistributedPistolScout(DistributedPistol):
    WeaponViewModel = "models/weapons/v_pistol_scout"

    def __init__(self):
        DistributedPistol.__init__(self)
        self.maxAmmo = 36
        self.ammo = self.maxAmmo

if not IS_CLIENT:
    DistributedPistolAI = DistributedPistol
    DistributedPistolAI.__name__ = 'DistributedPistolAI'
    DistributedPistolEngineerAI = DistributedPistolEngineer
    DistributedPistolEngineerAI.__name__ = 'DistributedPistolEngineerAI'
    DistributedPistolScoutAI = DistributedPistolScout
    DistributedPistolScoutAI.__name__ = 'DistributedPistolScoutAI'


from .TFWeaponGun import TFWeaponGun

from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponMode, TFWeaponType
from tf.tfbase.TFGlobals import DamageType

class DistributedShotgun(TFWeaponGun):

    WeaponModel = "models/weapons/c_shotgun"
    UsesViewModel = True

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

    def getReloadSound(self):
        return "Weapon_Shotgun.WorldReload"

class DistributedShotgunSecondary(DistributedShotgun):

    def __init__(self):
        DistributedShotgun.__init__(self)
        self.weaponType = TFWeaponType.Secondary
        # The heavy, soldier, and pyro shotguns (secondary) have a smaller
        # view kick than the engineer shotgun (primary).
        self.weaponData[TFWeaponMode.Primary]['punchAngle'] = 2.0

class DistributedShotgunEngineer(DistributedShotgun):
    WeaponViewModel = "models/weapons/v_shotgun_engineer"

class DistributedShotgunSoldier(DistributedShotgunSecondary):
    WeaponViewModel = "models/weapons/v_shotgun_soldier"

class DistributedShotgunHeavy(DistributedShotgunSecondary):
    WeaponViewModel = "models/weapons/v_shotgun_heavy"

class DistributedShotgunPyro(DistributedShotgunSecondary):
    WeaponViewModel = "models/weapons/v_shotgun_pyro"

class DistributedScattergunScout(DistributedShotgun):
    WeaponModel = "models/weapons/w_scattergun"
    WeaponViewModel = "models/weapons/v_scattergun_scout"

    def getName(self):
        return TFLocalizer.ScatterGun

    def getSingleSound(self):
        return "Weapon_Scatter_Gun.Single"

    def getEmptySound(self):
        return "Weapon_Scatter_Gun.Empty"

    def getReloadSound(self):
        return "Weapon_Scatter_Gun.WorldReload"

if not IS_CLIENT:
    DistributedShotgunAI = DistributedShotgun
    DistributedShotgunAI.__name__ = 'DistributedShotgunAI'
    DistributedShotgunSecondaryAI = DistributedShotgunSecondary
    DistributedShotgunSecondaryAI.__name__ = 'DistributedShotgunSecondaryAI'
    DistributedShotgunEngineerAI = DistributedShotgunEngineer
    DistributedShotgunEngineerAI.__name__ = 'DistributedShotgunEngineerAI'
    DistributedShotgunSoldierAI = DistributedShotgunSoldier
    DistributedShotgunSoldierAI.__name__ = 'DistributedShotgunSoldierAI'
    DistributedShotgunHeavyAI = DistributedShotgunHeavy
    DistributedShotgunHeavyAI.__name__ = 'DistributedShotgunHeavyAI'
    DistributedShotgunPyroAI = DistributedShotgunPyro
    DistributedShotgunPyroAI.__name__ = 'DistributedShotgunPyroAI'
    DistributedScattergunScoutAI = DistributedScattergunScout
    DistributedScattergunScoutAI.__name__ = 'DistributedScattergunScoutAI'


from tf.tfbase import TFLocalizer
from tf.tfbase.TFGlobals import DamageType

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFProjectileType, TFWeaponMode


class DistributedRocketLauncher(TFWeaponGun):

    WeaponModel = "models/weapons/c_rocketlauncher"
    WeaponViewModel = "models/weapons/v_rocketlauncher_soldier"
    UsesViewModel = True

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.reloadsSingly = True
        self.usesClip = True
        self.usesAmmo = True
        self.maxAmmo = 20
        self.maxClip = 4
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.primaryAttackInterval = 0.8
        self.weaponData[TFWeaponMode.Primary]['damage'] = 90
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['timeIdle'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['timeIdleEmpty'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['timeReloadStart'] = 0.1
        self.weaponData[TFWeaponMode.Primary]['timeReload'] = 0.83
        self.weaponData[TFWeaponMode.Primary]['projectile'] = TFProjectileType.Rocket
        self.damageType = DamageType.Blast | DamageType.HalfFalloff | DamageType.UseDistanceMod

    if IS_CLIENT:

        def doFireEffects(self):
            TFWeaponGun.doFireEffects(self)
            if not self.isOwnedByLocalPlayer():
                from direct.interval.IntervalGlobal import Func, Sequence, Wait
                from tf.tfbase import TFEffects
                node = self.find("**/backblast")
                if not node.isEmpty():
                    effect = TFEffects.getRocketBackBlastEffect()
                    effect.setInput(0, node, False)
                    effect.start(base.dynRender)
                    Sequence(Wait(0.1), Func(effect.softStop)).start()

    def getName(self):
        return TFLocalizer.RocketLauncher

    def getSingleSound(self):
        return "Weapon_RPG.Single"

    def getReloadSound(self):
        return "Weapon_RPG.WorldReload"

if not IS_CLIENT:
    DistributedRocketLauncherAI = DistributedRocketLauncher
    DistributedRocketLauncherAI.__name__ = 'DistributedRocketLauncherAI'

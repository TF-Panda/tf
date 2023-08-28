"""DistributedStickyBombLauncher module: contains the DistributedStickyBombLauncher class."""

from tf.actor.Activity import Activity
from tf.player.InputButtons import InputFlag
from tf.tfbase import TFLocalizer
from tf.tfbase.TFGlobals import DamageType

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFProjectileType, TFWeaponMode, TFWeaponType


class DistributedStickyBombLauncher(TFWeaponGun):

    WeaponModel = "models/weapons/w_stickybomb_launcher"
    WeaponViewModel = "models/weapons/v_stickybomb_launcher_demo"
    UsesViewModel = True
    MinViewModelOffset = (10, 0, -10)

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.weaponType = TFWeaponType.Secondary
        self.primaryAttackInterval = 0.6
        self.weaponData[TFWeaponMode.Primary].update({
          'damage': 120,
          'damageRadius': 146,
          'bulletsPerShot': 1,
          'spread': 0.0,
          'punchAngle': 3.0,
          'timeFireDelay': 0.6,
          'timeIdle': 0.6,
          'timeIdleEmpty': 0.6,
          'timeReloadStart': 0.1,
          'timeReload': 0.67,
          'projectile': TFProjectileType.PipebombRemote
        })
        self.damageType = DamageType.Blast | DamageType.HalfFalloff

        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = True
        self.maxAmmo = 24
        self.ammo = self.maxAmmo
        self.maxClip = 8
        self.clip = self.maxClip

        self.charge = 0.0
        self.isCharging = False

        if IS_CLIENT:
            self.chargingSound = None

    if IS_CLIENT:
        def stopChargeSound(self):
            if self.chargingSound:
                self.chargingSound.stop()
                self.chargingSound = None

        def playChargeSound(self):
            self.stopChargeSound()
            self.chargingSound = self.player.emitSound("Weapon_StickyBombLauncher.ChargeUp")

        def addPredictionFields(self):
            TFWeaponGun.addPredictionFields(self)
            self.addPredictionField("charge", float, networked=True, tolerance=0.01)
            self.addPredictionField("isCharging", bool, networked=True)

    def deactivate(self):
        self.charge = 0.0
        self.isCharging = False
        if IS_CLIENT:
            self.stopChargeSound()
        TFWeaponGun.deactivate(self)

    def primaryAttack(self):
        if IS_CLIENT:
            self.stopChargeSound()
        TFWeaponGun.primaryAttack(self)
        self.charge = 0.0
        self.isCharging = False

    def itemPostFrame(self):
        idle = True
        if base.clockMgr.getTime() > self.nextPrimaryAttack and self.clip > 0:
            if (self.player.buttons & InputFlag.Attack1) and not self.inReload:
                if not self.isCharging:
                    self.isCharging = True
                    self.sendWeaponAnim(Activity.VM_Pre_Fire)
                    if IS_CLIENT:
                        self.playChargeSound()
                    self.charge = 0.0
                    idle = False
                else:
                    self.charge += base.clockMgr.getDeltaTime() * 0.25
                    self.charge = min(1.0, self.charge)
                    if self.charge >= 1:
                        # Hit full charge, auto fire.
                        self.primaryAttack()
                    idle = False
            elif not self.inReload and (self.player.buttonsReleased & InputFlag.Attack1):
                self.primaryAttack()
                idle = False

        if idle:
            TFWeaponGun.itemPostFrame(self)

    def getName(self):
        return TFLocalizer.StickyBombLauncher

    def getSingleSound(self):
        return "Weapon_StickyBombLauncher.Single"

    def getReloadSound(self):
        return "Weapon_StickyBombLauncher.WorldReload"

if not IS_CLIENT:
    DistributedStickyBombLauncherAI = DistributedStickyBombLauncher
    DistributedStickyBombLauncherAI.__name__ = 'DistributedStickyBombLauncherAI'

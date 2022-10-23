"""DistributedFlameThrower module: contains the DistributedFlameThrower class."""

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFWeaponMode, TFWeaponType

from tf.player.InputButtons import InputFlag
from tf.actor.Actor import Actor
from tf.actor.Activity import Activity
from tf.tfbase import TFLocalizer, Sounds

class DistributedFlameThrower(TFWeaponGun):

    WeaponModel = "models/weapons/c_flamethrower"
    WeaponViewModel = "models/weapons/c_flamethrower"
    UsesViewModel = False

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesClip = False
        self.usesAmmo = True
        self.maxAmmo = 200
        self.ammo = self.maxAmmo
        self.primaryAttackInterval = 0.105
        self.weaponData[TFWeaponMode.Primary].update({
          'timeFireDelay': 0.105,
          'timeIdle': 0.6,
          'timeIdleEmpty': 0.6
        })

        self.isFiring = False
        self.wasFiring = False
        self.startFireTime = 0.0

        self.currFireSound = -1
        self.firingSound = None

        self.pilotLight = None
        self.pilotLightVM = None

    if IS_CLIENT:
        def generate(self):
            TFWeaponGun.generate(self)
            self.pilotLight = Actor()
            self.pilotLight.loadModel("models/weapons/c_flamethrower_pilotlight", False)
            self.pilotLightVM = Actor()
            self.pilotLightVM.loadModel("models/weapons/c_flamethrower_pilotlight", False)

        def disable(self):
            if self.pilotLight:
                self.pilotLight.cleanup()
                self.pilotLight = None
            if self.pilotLightVM:
                self.pilotLightVM.cleanup()
                self.pilotLightVM = None
            TFWeaponGun.disable(self)

        def preDataUpdate(self):
            TFWeaponGun.preDataUpdate(self)
            if not self.predictable:
                self.wasFiring = self.isFiring

        def addPredictionFields(self):
            TFWeaponGun.addPredictionFields(self)
            self.addPredictionField("isFiring", bool, networked=True)
            self.addPredictionField("startFireTime", float, networked=True, tolerance=0.01)
            self.addPredictionField("wasFiring", bool, networked=False)

        def emitSoundWpn(self, sndName, loop=False, chan=None):
            if self.isOwnedByLocalPlayer():
                return self.emitSound(sndName, loop=loop, chan=chan)
            else:
                return self.emitSoundSpatial(sndName, (0, 0, 30), loop=loop, chan=chan)

        def __weaponSoundUpdateTask(self, task):
            self.weaponSoundUpdate()
            return task.cont

        def weaponSoundUpdate(self):

            loop = False
            sound = -1
            if self.isFiring:
                elapsed = globalClock.frame_time - self.startFireTime
                if elapsed < 3:
                    sound = 0
                    sndName = "Weapon_FlameThrower.FireStart"
                else:
                    sound = 1
                    sndName = "Weapon_FlameThrower.FireLoop"
                    loop = True
            elif self.wasFiring:
                sound = 2
                sndName = "Weapon_FlameThrower.FireEnd"

            if sound != -1 and sound != self.currFireSound:
                if self.firingSound:
                    self.firingSound.stop()
                    self.firingSound = None
                self.firingSound = self.emitSoundWpn(sndName, loop=loop)
                self.currFireSound = sound

    def getName(self):
        return TFLocalizer.FlameThrower

    def activate(self):
        TFWeaponGun.activate(self)
        self.isFiring = False
        self.startFireTime = 0.0
        if IS_CLIENT:
            if not self.isOwnedByLocalPlayer() or base.cr.prediction.isFirstTimePredicted():
                self.emitSoundWpn("Weapon_FlameThrower.PilotLoop")

            if not self.isOwnedByLocalPlayer():
                self.addTask(self.__weaponSoundUpdateTask, 'flameThrowerSoundUpdate', appendTask=True, sim=True)
                if self.player:
                    self.pilotLight.modelNp.reparentTo(self.player)
                    self.pilotLight.setJointMergeParent(self.player)
            else:
                if self.viewModel:
                    self.pilotLightVM.modelNp.reparentTo(self.viewModel)
                    self.pilotLightVM.setJointMergeParent(self.viewModel)

    def deactivate(self):
        if IS_CLIENT:
            if self.firingSound:
                self.firingSound.stop()
                self.firingSound = None
            self.currFireSound = -1
            self.removeTask('flameThrowerSoundUpdate')
            if self.isOwnedByLocalPlayer():
                self.pilotLightVM.modelNp.reparentTo(base.hidden)
            else:
                self.pilotLight.modelNp.reparentTo(base.hidden)
        self.isFiring = False
        self.startFireTime = 0.0
        TFWeaponGun.deactivate(self)

    def primaryAttack(self):
        self.nextPrimaryAttack = globalClock.frame_time + self.primaryAttackInterval

    def itemPostFrame(self):
        self.wasFiring = self.isFiring

        if self.ammo > 0 and (self.player.buttons & InputFlag.Attack1):
            if not self.isFiring and globalClock.frame_time >= self.nextPrimaryAttack:
                self.isFiring = True
                self.startFireTime = globalClock.frame_time
                self.sendWeaponAnim(Activity.VM_Fire)

        elif self.isFiring:
            self.sendWeaponAnim(Activity.VM_Idle)
            self.isFiring = False

        TFWeaponGun.itemPostFrame(self)

        if IS_CLIENT:
            if base.cr.prediction.isFirstTimePredicted():
                self.weaponSoundUpdate()

if not IS_CLIENT:
    DistributedFlameThrowerAI = DistributedFlameThrower
    DistributedFlameThrowerAI.__name__ = 'DistributedFlameThrowerAI'

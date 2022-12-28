"""DMinigun module: contains the DMinigun class"""

# Do I hear boss music?

from panda3d.core import *

from .TFWeaponGun import TFWeaponGun

from .WeaponMode import TFWeaponMode, TFWeaponType
from tf.tfbase.TFGlobals import DamageType
from tf.player.InputButtons import InputFlag
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.tfbase import TFGlobals, TFLocalizer
from tf.actor.Activity import Activity
from tf.tfbase import Sounds

import math

MG_STATE_IDLE = 0
MG_STATE_STARTFIRING = 1
MG_STATE_FIRING = 2
MG_STATE_SPINNING = 3
MG_STATE_DRYFIRE = 4

MAX_BARREL_SPIN_VELOCITY = 20
BARREL_WIND_DOWN_SPEED = 6.666667 # 3 seconds to wind down.
BARREL_WIND_UP_SPEED = 20 # 1 second to wind up.

class DMinigun(TFWeaponGun):

    WeaponModel = "models/weapons/c_minigun"
    WeaponViewModel = "models/weapons/v_minigun_heavy"
    UsesViewModel = True

    SoundWindUp = 0
    SoundWindDown = 1
    SoundFire = 2
    SoundSpin = 3
    SoundDryFire = 4

    Sounds = {
        SoundWindUp: "Weapon_Minigun.WindUp",
        SoundWindDown: "Weapon_Minigun.WindDown",
        SoundFire: "Weapon_Minigun.Fire",
        SoundSpin: "Weapon_Minigun.Spin",
        SoundDryFire: "Weapon_Shotgun.Empty"
    }

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesAmmo = True
        self.usesClip = False
        #self.clip = -1
        self.reloadsSingly = False
        self.maxAmmo = 200
        self.ammo = self.maxAmmo
        self.weaponType = TFWeaponType.Primary
        self.primaryAttackInterval = 0.1
        self.staggerTracers = True
        self.damageType = DamageType.Bullet | DamageType.UseDistanceMod
        self.weaponData[TFWeaponMode.Primary].update({
            'spread': 0.08,
            'damage': 9,
            'range': 8192,
            'timeFireDelay': 0.1,
            'bulletsPerShot': 4
        })
        self.weaponReset()
        self.tracerSpread = 8.0

        if IS_CLIENT:
            #self.muzzleFlash = Actor()
            #self.muzzleFlash.loadModel("models/effects/minigunmuzzle", False)
            #self.muzzleFlash.modelNp.setSy(0.75)
            self.muzzleFlash = loader.loadModel("models/effects/minigunmuzzle")
            self.muzzleFlashLight = qpLight(qpLight.TPoint)
            self.muzzleFlashLight.setAttenuation(1, 0, 0.001)
            self.muzzleFlashLight.setAttenuationRadius(256)
            self.muzzleFlashLightColor = Vec3(1, 0.7, 0) * 2

    def getName(self):
        return TFLocalizer.Minigun

    def weaponReset(self):
        self.weaponMode = TFWeaponMode.Primary
        self.startedFiringAt = -1
        self.barrelCurrVelocity = 0.0
        self.barrelTargetVelocity = 0.0
        self.barrelAngle = 0.0
        self.barrelAccelSpeed = BARREL_WIND_UP_SPEED
        self.currSoundId = -1
        self.currSound = None
        self.weaponState = MG_STATE_IDLE

        self.worldBarrel = None
        self.viewBarrel = None

    def doFireEffects(self):
        pass

    if IS_CLIENT:

        def addPredictionFields(self):
            """
            Called when initializing an entity for prediction.

            This method should define fields that should be predicted
            for this entity.
            """

            TFWeaponGun.addPredictionFields(self)

            self.addPredictionField("weaponState", int)
            self.addPredictionField("barrelTargetVelocity", float)
            self.addPredictionField("barrelAccelSpeed", float)

        def announceGenerate(self):
            TFWeaponGun.announceGenerate(self)
            self.addTask(self.__updateMinigunBarrel, "updateMinigunBarrel", sim = False, appendTask = True)

        def disable(self):
            if self.muzzleFlash:
                self.muzzleFlash.removeNode()
                self.muzzleFlash = None
            self.worldBarrel = None
            if self.viewBarrel:
                self.viewBarrel.removeNode()
                self.viewBarrel = None
            self.stopWeaponSound()
            TFWeaponGun.disable(self)

        def __updateMinigunBarrel(self, task):
            if self.barrelCurrVelocity != self.barrelTargetVelocity:
                # Update barrel velocity to bing it up to speed or to rest
                self.barrelCurrVelocity = TFGlobals.approach(self.barrelTargetVelocity,
                    self.barrelCurrVelocity, self.barrelAccelSpeed * globalClock.dt)

            #print("barrel curr vel", self.barrelCurrVelocity)
            #print("barrel target", self.barrelTargetVelocity)

            # Update the barrel rotation based on current velo.
            self.barrelAngle += self.barrelCurrVelocity * globalClock.dt

            #print("barrel angle", self.barrelAngle)

            barrelAngleDeg = rad2Deg(self.barrelAngle)
            # Update view and world model control joints with new angle.
            if self.worldBarrel:
                self.worldBarrel.setH(barrelAngleDeg)
            if self.viewBarrel:
                self.viewBarrel.setP(barrelAngleDeg)
            if self.muzzleFlash:
                self.muzzleFlash.setR(-barrelAngleDeg)

            if not self.isOwnedByLocalPlayer():
                self.weaponSoundUpdate()

            return task.cont

        def onModelChanged(self):
            TFWeaponGun.onModelChanged(self)
            self.barrelAngle = 0
            self.barrelCurrVelocity = 0
            self.barrelTargetVelocity = 0
            self.barrelAccelSpeed = BARREL_WIND_UP_SPEED
            self.worldBarrel = self.controlJoint(None, "barrel")

        def stopWeaponSound(self):
            if self.currSound:
                self.currSound.stop()
                self.currSound = None

        def startMuzzleFlash(self):
            self.stopMuzzleFlash()

            if self.isOwnedByLocalPlayer() and self.viewModel:
                muzzle = self.viewModel.find("**/muzzle")
                self.muzzleFlash.setScale(0.65)
            else:
                muzzle = self.find("**/muzzle")
                self.muzzleFlash.setScale(1)
            if not muzzle.isEmpty():
                self.muzzleFlash.reparentTo(muzzle)
                base.addDynamicLight(self.muzzleFlashLight, followParent=muzzle)
                self.addTask(self.__muzzleFlashLightUpdate, 'muzzleFlashLightUpdate', sim=False, appendTask=True)

        def __muzzleFlashLightUpdate(self, task):
            bias = 0.3
            frac = math.sin(globalClock.frame_time * 50) * 0.5 + 0.5
            self.muzzleFlashLight.setColorSrgb(self.muzzleFlashLightColor * (frac * bias + (1.0 - bias)))
            return task.cont

        def stopMuzzleFlash(self):
            self.muzzleFlash.detachNode()
            self.removeTask('muzzleFlashLightUpdate')
            base.removeDynamicLight(self.muzzleFlashLight)

        def weaponSoundUpdate(self):
            if base.cr.prediction.hasBeenPredicted():
                return

            sound = -1
            loop = False
            if self.weaponState == MG_STATE_IDLE:
                if self.barrelCurrVelocity > 0:
                    sound = self.SoundWindDown
                    #if IS_CLIENT:
                    #    if self.barrelTargetVelocity > 0:
                    #        self.barrelTargetVelocity = 0
                else:
                    sound = -1
            elif self.weaponState == MG_STATE_STARTFIRING:
                sound = self.SoundWindUp
            elif self.weaponState == MG_STATE_FIRING:
                sound = self.SoundFire
                loop = True
            elif self.weaponState == MG_STATE_SPINNING:
                sound = self.SoundSpin
                loop = True
            elif self.weaponState == MG_STATE_DRYFIRE:
                sound = self.SoundDryFire
                loop = True

            if sound == self.currSoundId:
                return

            if self.weaponState == MG_STATE_FIRING:
                self.startMuzzleFlash()
            else:
                self.stopMuzzleFlash()

            self.stopWeaponSound()

            self.currSoundId = sound
            if self.currSoundId == -1:
                return

            spatialize = not self.isOwnedByLocalPlayer()
            if spatialize:
                self.currSound = self.emitSoundSpatial(self.Sounds[sound], (0, 0, 30), loop=loop)
            else:
                self.currSound = self.emitSound(self.Sounds[sound], loop=loop)

    def windUp(self):
        if not self.player:
            return

        # Play wind-up animation and sound
        self.sendWeaponAnim(Activity.VM_Pre_Fire)

        # Set the appropriate firing state
        self.weaponState = MG_STATE_STARTFIRING

        if IS_CLIENT:
            self.weaponSoundUpdate()

        self.player.setCondition(self.player.CondAiming)
        self.player.updateClassSpeed()

        # TODO: update player's speed

    # TODO: canHoslter(), can't holster if winding down

    def windDown(self):
        if not self.player:
            return

        self.sendWeaponAnim(Activity.VM_Post_Fire)

        # Set the appropriate firing state.
        self.weaponState = MG_STATE_IDLE
        if IS_CLIENT:
            self.weaponSoundUpdate()

        self.player.removeCondition(self.player.CondAiming)

        # Time to weapon idle.
        self.timeWeaponIdle = globalClock.frame_time + 2

        self.player.updateClassSpeed()

        # TODO: update player's speed

        self.barrelTargetVelocity = 0
        self.barrelAccelSpeed = BARREL_WIND_DOWN_SPEED

    def weaponIdle(self):
        now = globalClock.frame_time

        if now < self.timeWeaponIdle:
            return

        # Always wind down if we've hit here, because it only happens if the player
        # has stopped firing/spinning.
        if self.weaponState != MG_STATE_IDLE:
            if self.player:
                self.player.doAnimationEvent(PlayerAnimEvent.AttackPost)
            self.windDown()
            return

        TFWeaponGun.weaponIdle(self)

        self.timeWeaponIdle = now + 12.5 # How long till we do this again.

    def sendWeaponAnim(self, act):
        if True:#IS_CLIENT:
            # Client procedurally animates the barrel joint.
            if act == Activity.VM_Fire or \
                act == Activity.VM_Pre_Fire:

                self.barrelTargetVelocity = MAX_BARREL_SPIN_VELOCITY
                self.barrelAccelSpeed = BARREL_WIND_UP_SPEED

            elif act == Activity.VM_Post_Fire:
                self.barrelTargetVelocity = 0
                self.barrelAccelSpeed = BARREL_WIND_DOWN_SPEED

        # When we start firing, play the startup anim first.
        if act == Activity.VM_Fire:
            # If we're already playing the fire anim, let it continue.
            if self.activity == Activity.VM_Fire:
                return True

            # Otherwise, play from the start
            return TFWeaponGun.sendWeaponAnim(self, Activity.VM_Fire)

        return TFWeaponGun.sendWeaponAnim(self, act)

    def handleFireOnEmpty(self):
        if self.weaponState in [MG_STATE_FIRING, MG_STATE_SPINNING]:
            self.weaponState = MG_STATE_DRYFIRE
            self.sendWeaponAnim(Activity.VM_SecondaryFire)
            if self.weaponMode == TFWeaponMode.Secondary:
                self.weaponState = MG_STATE_SPINNING

    def primaryAttack(self):
        self.sharedAttack()

    def secondaryAttack(self):
        self.sharedAttack()

    def sharedAttack(self):
        if not self.player:
            return

        #if not self.canAttack():
        #    self.weaponIdle()
        #    return

        if self.player.buttons & InputFlag.Attack1:
            self.weaponMode = TFWeaponMode.Primary
        elif self.player.buttons & InputFlag.Attack2:
            self.weaponMode = TFWeaponMode.Secondary

        now = globalClock.frame_time

        if self.weaponState == MG_STATE_IDLE:
            self.windUp()
            self.nextPrimaryAttack = now + 1
            self.nextSecondaryAttack = now + 1
            self.timeWeaponIdle = now + 1
            self.startedFiringAt = -1
            self.player.doAnimationEvent(PlayerAnimEvent.AttackPre)

        elif self.weaponState == MG_STATE_STARTFIRING:
            # Start playing the looping fire sound
            if self.nextPrimaryAttack <= now:
                if self.weaponMode == TFWeaponMode.Secondary:
                    self.weaponState = MG_STATE_SPINNING
                else:
                    self.weaponState = MG_STATE_FIRING
                self.nextSecondaryAttack = self.nextPrimaryAttack = self.timeWeaponIdle = now

        elif self.weaponState == MG_STATE_FIRING:
            if self.weaponMode == TFWeaponMode.Secondary:
                self.weaponState = MG_STATE_SPINNING
                self.nextSecondaryAttack = self.nextPrimaryAttack = self.timeWeaponIdle = now

            elif self.ammo <= 0:
                self.weaponState = MG_STATE_DRYFIRE

            else:
                if self.startedFiringAt < 0:
                    self.startedFiringAt = now

                # Only fire if we're actually shooting.
                TFWeaponGun.primaryAttack(self) # Fire and do timers
                self.player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)
                self.timeWeaponIdle = now + 0.2

        elif self.weaponState == MG_STATE_DRYFIRE:
            self.startedFiringAt = -1
            if self.ammo > 0:
                self.weaponState = MG_STATE_FIRING
            elif self.weaponMode == TFWeaponMode.Secondary:
                self.weaponState = MG_STATE_SPINNING
            self.sendWeaponAnim(Activity.VM_SecondaryFire)

        elif self.weaponState == MG_STATE_SPINNING:
            self.startedFiringAt = -1
            if self.weaponMode == TFWeaponMode.Primary:
                if self.ammo > 0:
                    self.weaponState = MG_STATE_FIRING
                else:
                    self.weaponState = MG_STATE_DRYFIRE
            self.sendWeaponAnim(Activity.VM_SecondaryFire)

    def itemPostFrame(self):
        TFWeaponGun.itemPostFrame(self)
        if IS_CLIENT:
            self.weaponSoundUpdate()

    def activate(self):
        TFWeaponGun.activate(self)
        if IS_CLIENT and self.isOwnedByLocalPlayer():
            if self.player and self.player.viewModel:
                self.viewBarrel = self.player.viewModel.controlJoint(None, "v_minigun_barrel")

    def deactivate(self):
        if not IS_CLIENT or self.isOwnedByLocalPlayer():
            self.windDown()

        if IS_CLIENT and self.isOwnedByLocalPlayer():
            if self.viewBarrel:
                self.viewBarrel.removeNode()
                self.viewBarrel = None

        TFWeaponGun.deactivate(self)

if not IS_CLIENT:
    DMinigunAI = DMinigun
    DMinigunAI.__name__ = 'DMinigunAI'

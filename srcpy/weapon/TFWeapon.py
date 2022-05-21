if IS_CLIENT:
    from .DistributedWeapon import DistributedWeapon
    BaseClass = DistributedWeapon
else:
    from .DistributedWeaponAI import DistributedWeaponAI
    BaseClass = DistributedWeaponAI

from panda3d.core import Quat, Vec3

from .WeaponMode import TFWeaponMode, TFReloadMode, TFWeaponType, TFProjectileType
from .WeaponEffects import makeMuzzleFlash

from tf.actor.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.player.InputButtons import InputFlag

from tf.tfbase.TFGlobals import SolidFlag, SolidShape, remapVal

import math
import random

class TFWeapon(BaseClass):

    DropAmmo = True
    HiddenFromUI = False

    vmActTable = {
        TFWeaponType.Primary: {
            Activity.VM_Draw: Activity.Primary_VM_Draw,
            Activity.VM_Idle: Activity.Primary_VM_Idle,
            Activity.VM_Fire: Activity.Primary_VM_Fire,
            Activity.VM_Reload: Activity.Primary_VM_Reload,
            Activity.VM_Reload_Start: Activity.Primary_VM_Reload_Start,
            Activity.VM_Reload_Finish: Activity.Primary_VM_Reload_End,
            Activity.VM_SecondaryFire: Activity.Primary_VM_SecondaryFire,
            Activity.Attack_Stand_Prefire: Activity.Primary_Attack_Stand_Prefire,
            Activity.Attack_Stand_Postfire: Activity.Primary_Attack_Stand_Postfire
        },

        TFWeaponType.Secondary: {
            Activity.VM_Draw: Activity.Secondary_VM_Draw,
            Activity.VM_Idle: Activity.Secondary_VM_Idle,
            Activity.VM_Fire: Activity.Secondary_VM_Fire,
            Activity.VM_Reload: Activity.Secondary_VM_Reload,
            Activity.VM_Reload_Start: Activity.Secondary_VM_Reload_Start,
            Activity.VM_Reload_Finish: Activity.Secondary_VM_Reload_End
        },

        TFWeaponType.Melee: {
            Activity.VM_Draw: Activity.Melee_VM_Draw,
            Activity.VM_Idle: Activity.Melee_VM_Idle,
            Activity.VM_Fire: Activity.Melee_VM_Swing
        }
    }

    actTable = {
        TFWeaponType.Primary: {
            Activity.Stand: Activity.Primary_Stand,
            Activity.Run: Activity.Primary_Run,
            Activity.Crouch: Activity.Primary_Crouch,
            Activity.Crouch_Walk: Activity.Primary_Crouch_Walk,
            Activity.Swim: Activity.Primary_Swim,
            Activity.Air_Walk: Activity.Primary_Air_Walk,
            Activity.Jump: Activity.Primary_Jump,
            Activity.Jump_Start: Activity.Primary_Jump_Start,
            Activity.Jump_Float: Activity.Primary_Jump_Float,
            Activity.Jump_Land: Activity.Primary_Jump_Land,
            Activity.Double_Jump_Crouch: Activity.Primary_Double_Jump_Crouch,
            Activity.Attack_Stand: Activity.Primary_Attack_Stand,
            Activity.Attack_Stand_Prefire: Activity.Primary_Attack_Stand_Prefire,
            Activity.Attack_Stand_Postfire: Activity.Primary_Attack_Stand_Postfire,
            Activity.Attack_Crouch: Activity.Primary_Attack_Crouch,
            Activity.Attack_Crouch_Prefire: Activity.Primary_Attack_Crouch_Prefire,
            Activity.Attack_Crouch_Postfire: Activity.Primary_Attack_Crouch_Postfire,
            Activity.Attack_Swim: Activity.Primary_Attack_Swim,
            Activity.Attack_Swim_Prefire: Activity.Primary_Attack_Swim_Prefire,
            Activity.Attack_Swim_Postfire: Activity.Primary_Attack_Swim_Postfire,
            Activity.Attack_Air_Walk: Activity.Primary_Attack_Air_Walk,
            Activity.Attack_Air_Walk_Prefire: Activity.Primary_Attack_Air_Walk_Prefire,
            Activity.Attack_Air_Walk_Postfire: Activity.Primary_Attack_Air_Walk_Postfire,
            Activity.Reload_Stand: Activity.Primary_Reload_Stand,
            Activity.Reload_Stand_Loop: Activity.Primary_Reload_Stand_Loop,
            Activity.Reload_Stand_End: Activity.Primary_Reload_Stand_End,
            Activity.Reload_Crouch: Activity.Primary_Reload_Crouch,
            Activity.Reload_Crouch_Loop: Activity.Primary_Reload_Crouch_Loop,
            Activity.Reload_Crouch_End: Activity.Primary_Reload_Crouch_End,
            Activity.Reload_Swim: Activity.Primary_Reload_Swim,
            Activity.Reload_Swim_Loop: Activity.Primary_Reload_Swim_Loop,
            Activity.Reload_Swim_End: Activity.Primary_Reload_Swim_End,
            Activity.Reload_Air_Walk: Activity.Primary_Reload_Air_Walk,
            Activity.Reload_Air_Walk_Loop: Activity.Primary_Reload_Air_Walk_Loop,
            Activity.Reload_Air_Walk_End: Activity.Primary_Reload_Air_Walk_End,
            Activity.Deployed: Activity.Primary_Deployed,
            Activity.Deployed_Idle: Activity.Primary_Deployed_Idle,
            Activity.Deployed_Idle_Crouch: Activity.Primary_Deployed_Idle_Crouch,
            Activity.Gesture_Flinch: Activity.Primary_Gesture_Flinch
        },

        TFWeaponType.Secondary: {
            Activity.Stand: Activity.Secondary_Stand,
            Activity.Run: Activity.Secondary_Run,
            Activity.Crouch: Activity.Secondary_Crouch,
            Activity.Crouch_Walk: Activity.Secondary_Crouch_Walk,
            Activity.Swim: Activity.Secondary_Swim,
            Activity.Air_Walk: Activity.Secondary_Air_Walk,
            Activity.Jump: Activity.Secondary_Jump,
            Activity.Jump_Start: Activity.Secondary_Jump_Start,
            Activity.Jump_Float: Activity.Secondary_Jump_Float,
            Activity.Jump_Land: Activity.Secondary_Jump_Land,
            Activity.Double_Jump_Crouch: Activity.Secondary_Double_Jump_Crouch,
            Activity.Attack_Stand: Activity.Secondary_Attack_Stand,
            Activity.Attack_Crouch: Activity.Secondary_Attack_Crouch,
            Activity.Attack_Swim: Activity.Secondary_Attack_Swim,
            Activity.Attack_Air_Walk: Activity.Secondary_Attack_Air_Walk,
            Activity.Reload_Stand: Activity.Secondary_Reload_Stand,
            Activity.Reload_Stand_Loop: Activity.Secondary_Reload_Stand_Loop,
            Activity.Reload_Stand_End: Activity.Secondary_Reload_Stand_End,
            Activity.Reload_Crouch: Activity.Secondary_Reload_Crouch,
            Activity.Reload_Crouch_Loop: Activity.Secondary_Reload_Crouch_Loop,
            Activity.Reload_Crouch_End: Activity.Secondary_Reload_Crouch_End,
            Activity.Reload_Swim: Activity.Secondary_Reload_Swim,
            Activity.Reload_Swim_Loop: Activity.Secondary_Reload_Swim_Loop,
            Activity.Reload_Swim_End: Activity.Secondary_Reload_Swim_End,
            Activity.Reload_Air_Walk: Activity.Secondary_Reload_Air_Walk,
            Activity.Reload_Air_Walk_Loop: Activity.Secondary_Reload_Air_Walk_Loop,
            Activity.Reload_Air_Walk_End: Activity.Secondary_Reload_Air_Walk_End,
            Activity.Gesture_Flinch: Activity.Secondary_Gesture_Flinch
        },

        TFWeaponType.Melee: {
            Activity.Stand: Activity.Melee_Stand,
            Activity.Run: Activity.Melee_Run,
            Activity.Crouch: Activity.Melee_Crouch,
            Activity.Crouch_Walk: Activity.Melee_Crouch_Walk,
            Activity.Swim: Activity.Melee_Swim,
            Activity.Air_Walk: Activity.Melee_Air_Walk,
            Activity.Jump: Activity.Melee_Jump,
            Activity.Jump_Start: Activity.Melee_Jump_Start,
            Activity.Jump_Float: Activity.Melee_Jump_Float,
            Activity.Jump_Land: Activity.Melee_Jump_Land,
            Activity.Double_Jump_Crouch: Activity.Melee_Double_Jump_Crouch,
            Activity.Attack_Stand: Activity.Melee_Attack_Stand,
            Activity.Attack_Crouch: Activity.Melee_Attack_Crouch,
            Activity.Attack_Swim: Activity.Melee_Attack_Swim,
            Activity.Attack_Air_Walk: Activity.Melee_Attack_Air_Walk,
            Activity.Attack_Stand_SecondaryFire: Activity.Melee_Attack_Stand_SecondaryFire,
            Activity.Gesture_Flinch: Activity.Melee_Gesture_Flinch
        },

        TFWeaponType.PDA: {
            Activity.Stand: Activity.PDA_Stand,
            Activity.Run: Activity.PDA_Run,
            Activity.Crouch: Activity.PDA_Crouch,
            Activity.Crouch_Walk: Activity.PDA_Crouch_Walk,
            Activity.Swim: Activity.PDA_Swim,
            Activity.Air_Walk: Activity.PDA_Air_Walk,
            Activity.Jump: Activity.PDA_Jump,
            Activity.Jump_Start: Activity.PDA_Jump_Start,
            Activity.Jump_Float: Activity.PDA_Jump_Float,
            Activity.Jump_Land: Activity.PDA_Jump_Land,
            Activity.Gesture_Flinch: Activity.PDA_Gesture_Flinch
        },

        TFWeaponType.Building: {
            Activity.Stand: Activity.Building_Stand,
            Activity.Run: Activity.Building_Run,
            Activity.Crouch: Activity.Building_Crouch,
            Activity.Crouch_Walk: Activity.Building_Crouch_Walk,
            Activity.Swim: Activity.Building_Swim,
            Activity.Air_Walk: Activity.Building_Air_Walk,
            Activity.Jump: Activity.Building_Jump,
            Activity.Jump_Start: Activity.Building_Jump_Start,
            Activity.Jump_Float: Activity.Building_Jump_Float,
            Activity.Jump_Land: Activity.Building_Jump_Land,
            Activity.Gesture_Flinch: Activity.Building_Gesture_Flinch
        }
    }

    def __init__(self):
        BaseClass.__init__(self)
        self.weaponMode = TFWeaponMode.Primary
        self.reloadMode = TFReloadMode.Start
        self.inAttack = False
        self.inAttack2 = False
        self.currentAttackIsCrit = False
        self.lowered = False
        self.reloadStartClipAmount = 0
        self.critTime = 0.0
        self.lastCritCheckTime = 0.0
        self.lastCritCheckFrame = 0.0
        self.currentSeed = -1
        self.resetParity = False
        self.reloadedThroughAnimEvent = False
        self.weaponData = {
            TFWeaponMode.Primary: {
                'bulletsPerShot': 1,
                'ammoPerShot': 1,
                'spread': 0.0,
                'damage': 1,
                'range': 8192,
                'projectile': TFProjectileType.Bullet,
                'timeIdle': 1.0,
                'timeFireDelay': 1.0,
                'timeIdleEmpty': 0.0,
                'smackDelay': 0.5,
                'punchAngle': 0
            },
            TFWeaponMode.Secondary: {
                'bulletsPerShot': 1,
                'ammoPerShot': 1,
                'spread': 0.0,
                'damage': 1,
                'range': 8192,
                'projectile': TFProjectileType.Bullet,
                'timeIdle': 1.0,
                'timeFireDelay': 1.0,
                'timeIdleEmpty': 0.0,
                'smackDelay': 0.5,
                'punchAngle': 0
            }
        }

        self.weaponType = TFWeaponType.Primary

    if IS_CLIENT:
        def addPredictionFields(self):
            """
            Called when initializing an entity for prediction.

            This method should define fields that should be predicted
            for this entity.
            """

            BaseClass.addPredictionFields(self)

            # Add TF weapon prediction fields.
            self.addPredictionField("lowered", bool)
            self.addPredictionField("reloadMode", int)
            self.addPredictionField("reloadedThroughAnimEvent", bool)
            self.addPredictionField("weaponMode", int, networked=False)

        def getBobState(self):
            if not self.player:
                return None
            if self.player.isDead():
                return None
            vm = self.player.viewModel
            if not vm:
                return None
            return vm.bobState

        def calcViewModelBobHelper(self, player, bobState):
            if not bobState:
                return 0

            if globalClock.getDt() == 0.0 or not player:
                return 0

            cl_bobcycle = 0.8
            cl_bobup = 0.5

            speed = player.velocity.length()
            maxSpeedDelta = max(0.0, (globalClock.getFrameTime() - bobState.lastBobTime) * 320.0)

            # Don't allow too big speed changes
            speed = max(bobState.lastSpeed - maxSpeedDelta, min(bobState.lastSpeed + maxSpeedDelta, speed))
            speed = max(-320.0, min(320.0, speed))

            bobState.lastSpeed = speed

            bobOffset = remapVal(speed, 0.0, 320.0, 0.0, 1.0)

            bobState.bobTime += (globalClock.getFrameTime() - bobState.lastBobTime) * bobOffset
            bobState.lastBobTime = globalClock.getFrameTime()

            # Calculate the vertical bob
            cycle = bobState.bobTime - int(bobState.bobTime / cl_bobcycle) * cl_bobcycle
            cycle /= cl_bobcycle

            if cycle < cl_bobup:
                cycle = math.pi * cycle / cl_bobup
            else:
                cycle = math.pi + math.pi * (cycle - cl_bobup) / (1.0 - cl_bobup)

            bobState.verticalBob = speed * 0.005
            bobState.verticalBob = bobState.verticalBob * 0.3 + bobState.verticalBob * 0.7 * math.sin(cycle)
            bobState.verticalBob = max(-7.0, min(4.0, bobState.verticalBob))

            # Calculate the lateral bob
            cycle = bobState.bobTime - int(bobState.bobTime / cl_bobcycle * 2.0) * cl_bobcycle * 2.0
            cycle /= cl_bobcycle * 2.0

            if cycle < cl_bobup:
                cycle = math.pi * cycle / cl_bobup
            else:
                cycle = math.pi + math.pi * (cycle - cl_bobup) / (1.0 - cl_bobup)

            bobState.lateralBob = speed * 0.005
            bobState.lateralBob = bobState.lateralBob * 0.3 + bobState.lateralBob * 0.7 * math.sin(cycle)
            bobState.lateralBob = max(-7.0, min(4.0, bobState.lateralBob))

            return 0

        def addViewModelBobHelper(self, info, bobState):
            forward = info.angles.getForward()
            right = info.angles.getRight()

            # Apply bob, but scaled down to 40%
            info.origin += forward * (bobState.verticalBob * 0.4)

            # Z bob a bit more
            info.origin[2] += bobState.verticalBob * 0.1

            # Bob the angles
            hpr = info.angles.getHpr()
            hpr[2] += bobState.verticalBob * 0.5
            hpr[1] += bobState.verticalBob * 0.4
            hpr[0] -= bobState.lateralBob * 0.3
            info.angles.setHpr(hpr)

            info.origin += right * (bobState.lateralBob * 0.2)

        def calcViewModelBob(self):
            bobState = self.getBobState()
            if bobState:
                return self.calcViewModelBobHelper(self.player, bobState)
            else:
                return 0

        def addViewModelBob(self, viewModel, info):
            bobState = self.getBobState()
            if bobState:
                self.calcViewModelBob()
                self.addViewModelBobHelper(info, bobState)

    def translateViewModelActivity(self, activity):
        if self.UsesViewModel:
            return activity
        return self.vmActTable[self.weaponType].get(activity, activity)

    def translateActivity(self, activity):
        return self.actTable[self.weaponType].get(activity, activity)

    def activate(self):
        originalPrimaryAttack = self.nextPrimaryAttack
        deploy = True
        BaseClass.activate(self)

        if deploy:
            # overrides the anim length for calculating ready time.
            # Don't override primary attacks that are already further out than this.
            # This prevents people from exploiting weapons to allow weapons to fire
            # faster.
            deployTime = 0.67
            self.nextPrimaryAttack = max(originalPrimaryAttack, globalClock.getFrameTime() + deployTime)

        return True

    def primaryAttack(self):
        self.weaponMode = TFWeaponMode.Primary

        #if not self.canAttack():
        #    return

        BaseClass.primaryAttack(self)

        if not IS_CLIENT:
            self.player.pushExpression('specialAction')

        if self.reloadsSingly:
            self.reloadMode = TFReloadMode.Start

    def secondaryAttack(self):
        self.weaponMode = TFWeaponMode.Secondary

        # Don't hook secondary for now.

    def calcIsAttackCritical(self):
        return False

    def reload(self):
        if self.reloadMode == TFReloadMode.Start:
            if self.ammo <= 0:
                return False
            if self.clip >= self.maxClip:
                return False

        if self.reloadsSingly:
            return self.reloadSingly()

        self.defaultReload(self.maxClip, Activity.VM_Reload)

        return True

    def abortReload(self):
        BaseClass.abortReload(self)
        self.reloadMode = TFReloadMode.Start

    def reloadSingly(self):
        if self.nextPrimaryAttack > globalClock.getFrameTime():
            return False

        if not self.player:
            return False

        if self.reloadMode == TFReloadMode.Start:
            if self.sendWeaponAnim(Activity.VM_Reload_Start):
                self.setReloadTimer(self.viewModel.getChannelLength(self.viewModel.getCurrentChannel()))
            else:
                self.updateReloadTimers(True)

            self.reloadMode = TFReloadMode.Reloading

            self.reloadStartClipAmount = self.clip

            return True

        elif self.reloadMode == TFReloadMode.Reloading:
            if self.timeWeaponIdle > globalClock.getFrameTime():
                return False

            if self.clip == self.reloadStartClipAmount:
                self.player.doAnimationEvent(PlayerAnimEvent.Reload)
            else:
                self.player.doAnimationEvent(PlayerAnimEvent.ReloadLoop)

            self.reloadedThroughAnimEvent = False

            if self.sendWeaponAnim(Activity.VM_Reload):
                self.setReloadTimer(self.viewModel.getDuration())
            else:
                self.updateReloadTimers(False)

            if not IS_CLIENT:
                self.playSound(self.getReloadSound())

            self.reloadMode = TFReloadMode.ReloadingContinue
            return True

        elif self.reloadMode == TFReloadMode.ReloadingContinue:
            # Did we finish the reload start?  Now we can finish reloading the rocket.
            if self.timeWeaponIdle > globalClock.getFrameTime():
                return False

            # If we have ammo, remove ammo and add it to clip.
            if (self.ammo > 0 and not self.reloadedThroughAnimEvent):
                self.clip = min(self.clip + 1, self.maxClip)
                self.ammo -= 1

            if self.clip == self.maxClip or self.ammo <= 0:
                # Clip full or out of ammo to put in.
                self.reloadMode = TFReloadMode.Finish
            else:
                # Still reloading
                self.reloadMode = TFReloadMode.Reloading

            return True

        elif self.reloadMode == TFReloadMode.Finish:
            if self.sendWeaponAnim(Activity.VM_Reload_Finish):
                pass

            self.player.doAnimationEvent(PlayerAnimEvent.ReloadEnd)
            self.reloadMode = TFReloadMode.Start
            return True

    def operator_handleAnimEvent(self, event, operator):
        if event['event'] == AnimEvent.Weapon_IncrementAmmo:
            if self.ammo > 0 and not self.reloadedThroughAnimEvent:
                self.clip = min(self.clip + 1, self.maxClip)
                self.ammo -= 1
            self.reloadedThroughAnimEvent = True
            return

    def defaultReload(self, clipSize, activity):
        if not self.player:
            return False

        # Setup and check for reload.
        reloadPrimary = False
        reloadSecondary = False

        # If you don't have clips, then don't try to reload them.
        if self.usesClip:
            primary = min(clipSize - self.clip, self.ammo)
            if primary != 0:
                reloadPrimary = True

        if self.usesClip2:
            secondary = min(clipSize2 - self.clip2, self.ammo2)
            if secondary != 0:
                reloadSecondary = True

        if not (reloadPrimary or reloadSecondary):
            return False

        if not IS_CLIENT:
            self.playSound(self.getReloadSound())

        # Play the player's reload animation
        self.player.doAnimationEvent(PlayerAnimEvent.Reload)

        reloadTime = 0.0
        if self.sendWeaponAnim(activity):
            reloadTime = self.viewModel.getDuration()
        else:
            # No reload animation. Use the script time.
            if reloadPrimary:
                reloadTime = self.weaponData[TFWeaponMode.Primary]['timeReload']
            else:
                reloadTime = self.weaponData[TFWeaponMode.Secondary]['timeReload']

        self.setReloadTimer(reloadTime)

        self.inReload = True

        return True

    def updateReloadTimers(self, start):
        # Starting a reload?
        if start:
            self.setReloadTimer(self.weaponData[self.weaponMode]['timeReloadStart'])
        else:
            self.setReloadTimer(self.weaponData[self.weaponMode]['timeReload'])

    def setReloadTimer(self, reloadTime):
        if not self.player:
            return

        time = globalClock.getFrameTime() + reloadTime
        # TODO: set next player attack time (weapon independent)
        self.nextPrimaryAttack = time

        # Set next idle time (based on reloading).
        self.timeWeaponIdle = time

    def sendReloadEvents(self):
        if not self.player:
            return

        self.player.doAnimationEvent(PlayerAnimEvent.Reload)

    def itemBusyFrame(self):
        BaseClass.itemBusyFrame(self)

        if not self.player:
            return

        if self.player.buttons & InputFlag.Attack2 and not self.inReload and not self.inAttack2:
            if self.player.doClassSpecialSkill():
                self.nextSecondaryAttack = globalClock.getFrameTime() + 0.5
            self.inAttack2 = True
        else:
            self.inAttack2 = False

        # Interrupt a reload on reload singly weapons.
        if self.reloadsSingly:
            if self.player.buttons & InputFlag.Attack1:
                if self.reloadMode != TFReloadMode.Start and self.clip > 0:
                    self.reloadMode = TFReloadMode.Start
                    self.inReload = False
                    self.player.nextAttack = globalClock.getFrameTime()
                    self.nextPrimaryAttack = globalClock.getFrameTime()

                    self.timeWeaponIdle = globalClock.getFrameTime() + self.weaponData[self.weaponMode]['timeIdle']

    def itemPostFrame(self):
        if not self.player:
            return

        # Debounce InAttack flags
        if self.inAttack and not (self.player.buttons & InputFlag.Attack1):
            self.inAttack = False
        if self.inAttack2 and not (self.player.buttons & InputFlag.Attack2):
            self.inAttack2 = False

        if self.lowered:
            return

        BaseClass.itemPostFrame(self)

        if self.reloadsSingly:
            self.reloadSinglyPostFrame()

    def reloadSinglyPostFrame(self):
        if self.timeWeaponIdle > globalClock.getFrameTime():
            return

        # If the clip is empty and we have ammo remaining
        if (self.clip == 0 and self.ammo > 0) or (self.reloadMode != TFReloadMode.Start):
            # Reload/continue reloading
            self.reload()

    def weaponIdle(self):
        if self.hasWeaponIdleTimeElapsed():
            if not (self.reloadsSingly and self.reloadMode != TFReloadMode.Start):
                self.sendWeaponAnim(Activity.VM_Idle)
                self.timeWeaponIdle = globalClock.getFrameTime() + self.viewModel.getDuration()

    if not IS_CLIENT:
        def dropAsAmmoPack(self):
            """
            Creates a medium ammo pack using the weapon's model from the
            current position.
            """

            if not self.DropAmmo:
                # Don't drop if the weapon shouldn't drop ammo.
                return

            from .DWeaponDrop import DWeaponDropAI
            p = DWeaponDropAI()
            #p.skin = self.team
            p.solidShape = SolidShape.Model
            p.solidFlags |= SolidFlag.Tangible
            p.kinematic = False
            p.setModel(self.WeaponModel)
            # Make sure the weapon goes to sleep and doesn't jitter, because
            # the pickup only becomes active when it's asleep.
            p.node().setSleepThreshold(0.25)
            p.node().setCcdEnabled(True)
            p.singleUse = True
            p.packType = "med"

            # Give amount of metal player has at the time of dropping
            # up to a maximum of 100 and a minimum of 5.
            # For non-engineers, it will always give 100 metal.
            p.metalAmount = min(100, max(5, self.player.metal))

            # Match current weapon position/rotation in animation.
            p.setMat(self.character.getJointNetTransform(0) * self.characterNp.getMat(base.render))

            # Calculate initial impulse.
            q = Quat()
            q.setHpr(self.player.viewAngles)
            right = q.getRight()
            up = q.getUp()
            impulse = Vec3()
            impulse += up * random.uniform(-0.25, 0.25)
            impulse += right * random.uniform(-0.25, 0.25)
            impulse.normalize()
            impulse *= random.uniform(100, 150)
            impulse += self.player.velocity

            # Cap the impulse.
            speed = impulse.length()
            if speed > 300:
                impulse *= 300 / speed

            p.setMass(25.0)
            angImpulse = Vec3(random.uniform(0, 100), 0, 0)
            #p.node().setLinearVelocity(impulse)
            #p.node().setAngularVelocity(angImpulse)
            p.node().addForce(impulse, p.node().FTVelocityChange)
            p.node().addTorque(angImpulse, p.node().FTVelocityChange)

            base.net.generateObject(p, self.zoneId)
            #p.ls()

if not IS_CLIENT:
    # Server alias.
    TFWeaponAI = TFWeapon
    TFWeaponAI.__name__ = 'TFWeaponAI'

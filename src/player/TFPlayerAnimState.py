
from .TFClass import *
from tf.actor.Activity import Activity
from .PlayerAnimEvent import PlayerAnimEvent

from panda3d.core import *

from enum import IntEnum, auto

class GestureSlot(IntEnum):
    AttackAndReload = 1
    Grenade = 2
    Jump = 3
    Swim = 4
    Flinch = 5
    VCD = 6
    Custom = 7

    COUNT = auto()

class TFPlayerAnimState:

    def __init__(self, player):
        self.player = player
        self.vel = Vec3()
        self.forceAimYaw = False
        self.lastAimTurnTime = 0.0
        self.goalFeetYaw = 0.0
        self.currentFeetYaw = 0.0
        self.eyeYaw = 0.0
        self.currentMainSequenceActivity = Activity.Invalid
        self.specificMainSequence = -1
        self.inSwim = False
        self.inAirWalk = False
        self.jumping = False
        self.firstJumpFrame = False
        self.jumpStartTime = 0.0
        self.idealActivity = Activity.Invalid

    def isGestureSlotPlaying(self, slot, activity):
        return (not self.player.isCurrentChannelFinished(layer=slot)) and (self.player.getCurrentActivity(layer=slot) == activity)

    def restartGesture(self, slot, activity, autoKill = True, blendIn = 0.1, blendOut = 0.1):
        self.player.startChannel(act = self.translateActivity(activity),
                                 autoKill = autoKill, blendIn = blendIn, blendOut = blendOut,
                                 layer = slot)

    def doAnimationEvent(self, event, data):
        #print("anim event", event)
        from tf.weapon.DMinigun import DMinigun
        if event == PlayerAnimEvent.AttackPrimary:
            isMinigun = isinstance(self.player.getActiveWeaponObj(), DMinigun)
            if isMinigun:
                gestureActivity = Activity.Attack_Stand
                if not self.isGestureSlotPlaying(GestureSlot.AttackAndReload, self.translateActivity(gestureActivity)):
                    self.restartGesture(GestureSlot.AttackAndReload, gestureActivity)
            else:
                # Weapon primary fire.
                self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand)
        elif event == PlayerAnimEvent.AttackSecondary:
            # Weapon secondary fire.
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand_SecondaryFire)
        elif event == PlayerAnimEvent.AttackGrenade:
            # Grenade throw.
            pass
        elif event == PlayerAnimEvent.Reload:
            # TODO: crouching, swimming
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Reload_Stand, blendOut=0.0)
        elif event == PlayerAnimEvent.ReloadLoop:
            # TODO: crouching, swimming
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Reload_Stand_Loop, blendIn=0.0, blendOut=0.0)
        elif event == PlayerAnimEvent.ReloadEnd:
            # TODO: crouching, swimming
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Reload_Stand_End, blendIn=0.0)
        elif event == PlayerAnimEvent.Flinch:
            if not self.player.isChannelPlaying(layer=GestureSlot.Flinch):
                self.restartGesture(GestureSlot.Flinch, Activity.Gesture_Flinch)
        elif event == PlayerAnimEvent.Jump:
            self.jumping = True
            self.firstJumpFrame = True
            self.jumpStartTime = globalClock.getFrameTime()
            #self.restartMainSequence()
        elif event == PlayerAnimEvent.DoubleJump:
            if not self.jumping:
                self.jumping = True
                self.firstJumpFrame = True
                self.jumpStartTime = globalClock.getFrameTime()

            self.inAirWalk = False

            self.restartGesture(GestureSlot.Jump, Activity.Double_Jump)

        elif event == PlayerAnimEvent.AttackPre:
            isMinigun = isinstance(self.player.getActiveWeaponObj(), DMinigun)
            autoKill = False
            if isMinigun:
                autoKill = True
            #print("attack pre")
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand_Prefire, autoKill=autoKill)

        elif event == PlayerAnimEvent.AttackPost:
            #print("attack post")
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand_Postfire)

    def angleNormalize(self, ang):
        ang = ang % 360
        if ang > 180:
            ang -= 360
        if ang < -180:
            ang += 360
        return ang

    def computeAimPoseParam(self):
        moving = self.vel.length() > 1.0

        if moving or self.forceAimYaw:
            # Feet match the eye direction when moving.
            self.goalFeetYaw = self.eyeYaw
        else:
            # Initialize to feet.
            if self.lastAimTurnTime <= 0.0:
                self.goalFeetYaw = self.eyeYaw
                self.currentFeetYaw = self.eyeYaw
                self.lastAimTurnTime = globalClock.getFrameTime()
            else:
                yawDelta = self.angleNormalize(self.goalFeetYaw - self.eyeYaw)
                if abs(yawDelta) > 45:
                    side = -1.0 if yawDelta > 0.0 else 1.0
                    self.goalFeetYaw += 45 * side

        # Fix up the feet yaw
        self.goalFeetYaw = self.angleNormalize(self.goalFeetYaw)
        if self.goalFeetYaw != self.currentFeetYaw:
            if self.forceAimYaw:
                self.currentFeetYaw = self.goalFeetYaw
            else:
                self.currentFeetYaw = self.convergeYawAngles(
                    self.goalFeetYaw, 720.0, globalClock.getDt(), self.currentFeetYaw)
                self.lastAimTurnTime = globalClock.getFrameTime()

        # Rotate the body into position.
        angles = self.player.getHpr()
        angles[0] = self.currentFeetYaw
        self.player.setHpr(angles)

        # Find the aim (torso) yaw base on the eye and feet yaws.
        aimYaw = self.eyeYaw - self.currentFeetYaw
        aimYaw = self.angleNormalize(aimYaw)

        # Set the aim yaw and save.
        yawParam = self.player.getPoseParameter("body_yaw")
        if yawParam:
            yawParam.setValue(-aimYaw)
        #self.player.lookYaw = yawParam.getNormValue()
        #print(-aimYaw)

        # Turn off a force aim yaw - either we have already updated or we don't need to.
        self.forceAimYaw = False

    def convergeYawAngles(self, goalYaw, yawRate, deltaTime, currentYaw):
        fadeTurnDegrees = 60.0

        # Find the yaw delta.
        deltaYaw = goalYaw - currentYaw
        deltaYawAbs = abs(deltaYaw)
        deltaYaw = self.angleNormalize(deltaYaw)

        # Always do at least a bit of the turn (1%).
        scale = 1.0
        scale = deltaYawAbs / fadeTurnDegrees
        scale = max(0.01, min(1.0, scale))

        yaw = yawRate * deltaTime * scale
        if deltaYawAbs < yaw:
            currentYaw = goalYaw
        else:
            side = -1.0 if deltaYaw < 0.0 else 1.0
            currentYaw += (yaw * side)

        currentYaw = self.angleNormalize(currentYaw)

        return currentYaw

    def translateActivity(self, actDesired):
        translateActivity = actDesired
        if self.inSwim:
            if actDesired == Activity.Attack_Stand:
                translateActivity = Activity.Attack_Swim
            elif actDesired == Activity.Reload_Stand:
                translateActivity = Activity.Reload_Swim

        wpn = self.player.getActiveWeaponObj()
        if wpn:
            translateActivity = wpn.translateActivity(translateActivity)

        return translateActivity

    def calcMainActivity(self):
        self.idealActivity = Activity.Stand

        if self.handleJumping() or self.handleDucking() or self.handleSwimming():
            pass
        else:
            self.handleMoving()

        return self.idealActivity

    def restartMainSequence(self):
        if self.player:
            self.player.setAnimTime(globalClock.getFrameTime())
            self.player.setCycle(0.0)

    def handleJumping(self):
        # TODO: airwalk
        if False: # airwalk
            pass
        else:
            if self.jumping:
                if self.firstJumpFrame:
                    self.firstJumpFrame = False
                    #self.restartMainSequence()

                # TODO: reset after we hit water and start swimming.

                # Don't check if he's on the ground for a sec.. sometimes the
                # client still has the on-ground flag set right when the
                # message comes in.
                if globalClock.getFrameTime() - self.jumpStartTime > 0.2:
                    if self.player.onGround:
                        self.jumping = False
                        #self.restartMainSequence()

                        self.restartGesture(GestureSlot.Jump, Activity.Jump_Land)

                # If we're still jumping
                if self.jumping:
                    if globalClock.getFrameTime() - self.jumpStartTime > 0.5:
                        self.idealActivity = Activity.Jump_Float
                    else:
                        self.idealActivity = Activity.Jump_Start

        return self.jumping # or self.inAirWalk

    def handleDucking(self):
        return False

    def handleSwimming(self):
        return False

    def handleMoving(self):
        speed = self.vel.length()

        if self.player.inCondition(self.player.CondAiming):
            if speed > 0.5:
                self.idealActivity = Activity.Deployed
            else:
                self.idealActivity = Activity.Deployed_Idle
            return True
        elif speed > 0.5:
            self.idealActivity = Activity.Run
            return True
        return False

    def computeMainSequence(self):
        idealActivity = self.calcMainActivity()

        # Store our current activity
        self.currentMainSequenceActivity = idealActivity

        if self.specificMainSequence >= 0:
            if self.player.getCurrentChannel() != self.specificMainSequence:
                self.player.startChannel(self.specificMainSequence)
                return

            if not self.player.isChannelFinished():
                return

            self.specificMainSequence = -1
            self.restartMainSequence()

        animDesired = self.player.getChannelForActivity(self.translateActivity(idealActivity))
        if self.player.getChannelActivity(self.player.getCurrentChannel()) == self.player.getChannelActivity(animDesired):
            return

        if animDesired < 0:
            animDesired = 0

        self.player.startChannel(animDesired)

    def update(self):
        if self.player.isDead():
            return

        pitchParam = self.player.getPoseParameter("body_pitch")
        #yawParam = self.player.getPoseParameter("look_yaw")
        moveXParam = self.player.getPoseParameter("move_x")
        moveYParam = self.player.getPoseParameter("move_y")

        self.vel = -self.player.getVelocity()
        vel = self.vel

        self.eyeYaw = self.angleNormalize(self.player.eyeH * 360)
        self.eyePitch = self.angleNormalize(self.player.eyeP * 360)

        self.computeMainSequence()
        #self.computeGestureSequence()

        self.computeAimPoseParam()

        if pitchParam:
            pitchParam.setValue(self.eyePitch)
        #self.player.lookPitch = pitchParam.getNormValue()

        forwardSpeed = self.player.maxSpeed
        backwardSpeed = self.player.maxSpeed
        moveX = vel[0] / forwardSpeed
        moveY = vel[1] / forwardSpeed if vel[1] > 0 else vel[1] / backwardSpeed
        if moveXParam:
            moveXParam.setValue(moveX)
        if moveYParam:
            moveYParam.setValue(moveY)

        #self.player.moveX = moveXParam.getNormValue()
        #self.player.moveY = moveYParam.getNormValue()


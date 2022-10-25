
from .TFClass import *
from tf.actor.Activity import Activity
from .PlayerAnimEvent import PlayerAnimEvent

from panda3d.core import *

import math

class GestureSlot:
    AttackAndReload = 1
    Grenade = 2
    Jump = 3
    Swim = 4
    Flinch = 5
    VCD = 6
    Custom = 7

    COUNT = 7

class TFPlayerAnimState:

    LoserStateTable = {
        Activity.Stand: Activity.Loser_Stand,
        Activity.Run: Activity.Loser_Run,
        Activity.Crouch: Activity.Loser_Crouch,
        Activity.Air_Walk: Activity.Loser_Air_Walk,
        Activity.Jump: Activity.Loser_Jump,
        Activity.Jump_Start: Activity.Loser_Jump_Start,
        Activity.Jump_Float: Activity.Loser_Jump_Float,
        Activity.Jump_Land: Activity.Loser_Jump_Land,
        Activity.Swim: Activity.Loser_Swim,
        Activity.Double_Jump: Activity.Loser_Double_Jump
    }

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
        self.estimatedYaw = 0.0
        self.holdDeployedPoseUntilTime = 0.0
        self.initPoseParameters()

    def delete(self):
        self.player = None
        self.moveXParam = None
        self.moveYParam = None
        self.bodyPitchParam = None
        self.bodyYawParam = None
        self.vel = None

    def onPlayerModelChanged(self):
        self.gotPoseParameters = False
        self.holdDeployedPoseUntilTime = 0.0

    def initPoseParameters(self):
        self.moveXParam = self.player.getPoseParameter("move_x")
        self.moveYParam = self.player.getPoseParameter("move_y")
        self.bodyPitchParam = self.player.getPoseParameter("body_pitch")
        self.bodyYawParam = self.player.getPoseParameter("body_yaw")
        self.gotPoseParameters = True

    def isGestureSlotPlaying(self, slot, activity):
        return (not self.player.isAnimFinished(slot)) and (self.player.getCurrentAnimActivity(slot) == activity)

    def restartGesture(self, slot, activity, autoKill = True, blendIn = 0.1, blendOut = 0.1):
        self.player.setAnim(activity = self.translateActivity(activity, slot),
                                 autoKill = autoKill, blendIn = blendIn, blendOut = blendOut,
                                 layer = slot)

    def doAnimationEvent(self, event, data):
        #print("anim event", event)
        from tf.weapon.DMinigun import DMinigun
        from tf.weapon.DistributedSniperRifle import DistributedSniperRifle
        if event == PlayerAnimEvent.AttackPrimary:
            wpn = self.player.getActiveWeaponObj()
            isMinigun = isinstance(wpn, DMinigun)
            isSniperRifle = isinstance(wpn, DistributedSniperRifle)
            if isMinigun:
                gestureActivity = Activity.Attack_Stand
                if not self.isGestureSlotPlaying(GestureSlot.AttackAndReload, self.translateActivity(gestureActivity, GestureSlot.AttackAndReload)):
                    self.restartGesture(GestureSlot.AttackAndReload, gestureActivity)
            elif isSniperRifle and self.player.inCondition(self.player.CondZoomed):
                # Weapon primary fire, zoomed in.
                if self.player.ducking:
                    act = Activity.Deployed_Attack_Crouch
                else:
                    act = Activity.Deployed_Attack_Stand
                self.restartGesture(GestureSlot.AttackAndReload, act)
                self.holdDeployedPoseUntilTime = globalClock.frame_time + 2.0
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
            if self.inAirWalk:
                act = Activity.Reload_Air_Walk
            elif self.inSwim:
                act = Activity.Reload_Swim
            elif self.player.ducking:
                act = Activity.Reload_Crouch
            else:
                act = Activity.Reload_Stand
            self.restartGesture(GestureSlot.AttackAndReload, act, blendOut=0.0)
        elif event == PlayerAnimEvent.ReloadLoop:
            if self.inAirWalk:
                act = Activity.Reload_Air_Walk_Loop
            elif self.inSwim:
                act = Activity.Reload_Swim_Loop
            elif self.player.ducking:
                act = Activity.Reload_Crouch_Loop
            else:
                act = Activity.Reload_Stand_Loop
            self.restartGesture(GestureSlot.AttackAndReload, act, blendIn=0.0, blendOut=0.0)
        elif event == PlayerAnimEvent.ReloadEnd:
            if self.inAirWalk:
                act = Activity.Reload_Air_Walk_End
            elif self.inSwim:
                act = Activity.Reload_Swim_End
            elif self.player.ducking:
                act = Activity.Reload_Crouch_End
            else:
                act = Activity.Reload_Stand_End
            self.restartGesture(GestureSlot.AttackAndReload, act, blendIn=0.0)
        elif event == PlayerAnimEvent.Flinch:
            if not self.player.isAnimPlaying(GestureSlot.Flinch):
                self.restartGesture(GestureSlot.Flinch, self.translateActivity(Activity.Gesture_Flinch, GestureSlot.Flinch))
        elif event == PlayerAnimEvent.Jump:
            self.jumping = True
            self.firstJumpFrame = True
            self.jumpStartTime = globalClock.frame_time
            self.restartMainSequence()
        elif event == PlayerAnimEvent.DoubleJump:
            if not self.jumping:
                self.jumping = True
                self.firstJumpFrame = True
                self.jumpStartTime = globalClock.frame_time
                self.restartMainSequence()

            self.inAirWalk = False

            self.restartGesture(GestureSlot.Jump, Activity.Double_Jump)

        elif event == PlayerAnimEvent.AttackPre:
            isMinigun = isinstance(self.player.getActiveWeaponObj(), DMinigun)
            autoKill = False
            if isMinigun:
                autoKill = True
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand_Prefire, autoKill=autoKill)

        elif event == PlayerAnimEvent.AttackPost:
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand_Postfire)

    def angleNormalize(self, ang):
        ang = ang % 360
        if ang > 180:
            ang -= 360
        if ang < -180:
            ang += 360
        return ang

    def computeAimPoseParam(self):
        moving = self.vel.getXy().length() > 1.0

        if moving or self.forceAimYaw:
            # Feet match the eye direction when moving.
            self.goalFeetYaw = self.eyeYaw
        else:
            # Initialize to feet.
            if self.lastAimTurnTime <= 0.0:
                self.goalFeetYaw = self.eyeYaw
                self.currentFeetYaw = self.eyeYaw
                self.lastAimTurnTime = globalClock.frame_time
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
                    self.goalFeetYaw, 720.0, globalClock.dt, self.currentFeetYaw)
                self.lastAimTurnTime = globalClock.frame_time

        # Rotate the body into position.
        angles = self.player.getHpr()
        angles[0] = self.currentFeetYaw
        self.player.setHpr(angles)

        # Find the aim (torso) yaw base on the eye and feet yaws.
        aimYaw = self.eyeYaw - self.currentFeetYaw
        aimYaw = self.angleNormalize(aimYaw)

        # Set the aim yaw and save.
        if self.bodyYawParam:
            self.bodyYawParam.setValue(-aimYaw)
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

    def translateActivity(self, actDesired, layer=0):
        translateActivity = actDesired
        if self.inSwim:
            if actDesired == Activity.Attack_Stand:
                translateActivity = Activity.Attack_Swim
            elif actDesired == Activity.Reload_Stand:
                translateActivity = Activity.Reload_Swim

        if self.player.isLoser():
            translateActivity = self.LoserStateTable.get(translateActivity, translateActivity)
        else:
            wpn = self.player.getActiveWeaponObj()
            if wpn:
                translateActivity = wpn.translateActivity(translateActivity)

        chan = self.player.getChannelForActivity(translateActivity, layer=layer)
        if chan < 0:
            # Don't have a channel for this translated activity, use original.
            return actDesired

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
            self.player.setCycle(0.0)

    def handleJumping(self):
        classCanAirWalk = not self.player.classInfo.DontDoAirWalk

        if classCanAirWalk and (self.vel.z > 300.0 or self.inAirWalk):
            # Check to see if we were in an airwalk and now we are basically
            # on the ground.
            if self.player.onGround and self.inAirWalk:
                # Stop air walking.
                self.inAirWalk = False
                self.restartMainSequence()
                self.restartGesture(GestureSlot.Jump, Activity.Jump_Land)
            # TODO: handle water level
            elif not self.player.onGround:
                # If we're off the ground and moving up at a high enough
                # velocity, start air walking.
                self.idealActivity = Activity.Air_Walk
                self.inAirWalk = True
        else:
            if self.jumping:
                if self.firstJumpFrame:
                    self.firstJumpFrame = False
                    self.restartMainSequence()

                # TODO: reset after we hit water and start swimming.

                # Don't check if he's on the ground for a sec.. sometimes the
                # client still has the on-ground flag set right when the
                # message comes in.
                if globalClock.frame_time - self.jumpStartTime > 0.2:
                    if self.player.onGround:
                        self.jumping = False
                        self.restartMainSequence()

                        self.restartGesture(GestureSlot.Jump, Activity.Jump_Land)

                # If we're still jumping
                if self.jumping:
                    if globalClock.frame_time - self.jumpStartTime > 0.5:
                        self.idealActivity = Activity.Jump_Float
                    else:
                        self.idealActivity = Activity.Jump_Start

        return self.jumping or self.inAirWalk

    def handleDucking(self):
        return False

    def handleSwimming(self):
        return False

    def handleMoving(self):
        speed = self.vel.getXy().length()

        if speed > 0.5:
            self.holdDeployedPoseUntilTime = 0.0

        if self.player.inCondition(self.player.CondAiming):
            if speed > 0.5:
                self.idealActivity = Activity.Deployed
            else:
                self.idealActivity = Activity.Deployed_Idle
            return True
        elif self.holdDeployedPoseUntilTime > globalClock.frame_time:
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
            if self.player.getCurrentAnim() != self.specificMainSequence:
                self.player.setAnim(self.specificMainSequence)
                return

            if not self.player.isAnimFinished():
                return

            self.specificMainSequence = -1
            self.restartMainSequence()

        animDesired = self.player.getChannelForActivity(self.translateActivity(idealActivity))
        if self.player.getAnimActivity(self.player.getCurrentAnim()) == self.player.getAnimActivity(animDesired):
            return

        if animDesired < 0:
            animDesired = 0

        self.player.setAnim(animDesired)

    def computeMovePoseParam(self):
        self.estimateYaw()

        angle = self.angleNormalize(self.eyeYaw)

        # Calc side to side turning - the view vs. movement yaw.
        yaw = angle - self.estimatedYaw
        yaw = self.angleNormalize(-yaw)

        playbackRate, isMoving = self.calcMovementPlaybackRate()

        # Get the current speed the character is running.
        moveXVal = 0.0
        moveYVal = 0.0
        if isMoving:
            moveXVal = -math.cos(deg2Rad(yaw)) * playbackRate
            moveYVal = -math.sin(deg2Rad(yaw)) * playbackRate

        if self.moveXParam:
            self.moveXParam.setValue(moveXVal)
        if self.moveYParam:
            self.moveYParam.setValue(moveYVal)

    def calcMovementPlaybackRate(self):
        speed = self.vel.getXy().length()

        moving = (speed > 0.5)

        ret = 1.0
        if moving:
            groundSpeed = self.getCurrentMaxGroundSpeed()
            if groundSpeed < 0.001:
                ret = 0.01
            else:
                ret = speed / groundSpeed
                ret = max(0.01, min(10.0, ret))

        return (ret, moving)

    def getCurrentMaxGroundSpeed(self):
        if self.player.airDashing:
            return 1.0

        # Get current blend values and normalize it to get the max speed along
        # that blend direction.
        blendValues = Vec2()
        if self.moveXParam:
            blendValues.x = self.moveXParam.getValue()
        if self.moveYParam:
            blendValues.y = self.moveYParam.getValue()

        if blendValues.x == 0 and blendValues.y == 0:
            return 0.0

        blendDir = blendValues.normalized()

        # Get root motion speed along the normalized blend direction.
        if self.moveXParam:
            self.moveXParam.setValue(blendDir.x)
        if self.moveYParam:
            self.moveYParam.setValue(blendDir.y)

        bundle = self.player.character
        seq = bundle.getAnimLayer(0)._sequence
        if seq == -1:
            return 0.0

        chan = bundle.getChannel(seq)
        duration = max(0.01, chan.getLength(bundle))
        speed = chan.getRootMotionVector(bundle).getXy().length() / duration

        # Restore previous blend values.
        if self.moveXParam:
            self.moveXParam.setValue(blendValues.x)
        if self.moveYParam:
            self.moveYParam.setValue(blendValues.y)

        return speed

    def estimateYaw(self):
        dt = globalClock.dt
        if dt == 0.0:
            return

        angles = self.player.getHpr()

        if self.vel.x == 0.0 and self.vel.y == 0.0:
            # If we are not moving, sync up the feet and eyes slowly.
            yawDelta = angles[0] - self.estimatedYaw
            yawDelta = self.angleNormalize(yawDelta)
            if dt < 0.25:
                yawDelta *= (dt * 4.0)
            else:
                yawDelta *= dt
            self.estimatedYaw += yawDelta
            self.estimatedYaw = self.angleNormalize(self.estimatedYaw)
        else:
            self.estimatedYaw = (math.atan2(self.vel.y, self.vel.x) * 180.0 / math.pi)
            self.estimatedYaw = max(-180.0, min(180.0, self.estimatedYaw))

    def update(self):
        if self.player.isDead():
            return

        if not self.gotPoseParameters:
            self.initPoseParameters()

        self.vel = -self.player.getVelocity()
        vel = self.vel
        speed = vel.getXy().length()

        self.eyeYaw = self.angleNormalize(self.player.eyeH * 360)
        self.eyePitch = self.angleNormalize(self.player.eyeP * 360)

        self.computeMainSequence()
        self.computeMovePoseParam()

        self.computeAimPoseParam()

        if self.bodyPitchParam:
            self.bodyPitchParam.setValue(self.eyePitch)


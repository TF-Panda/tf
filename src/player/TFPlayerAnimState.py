
from .TFClass import *
from tf.character.Activity import Activity
from .PlayerAnimEvent import PlayerAnimEvent

from panda3d.core import *

from enum import IntEnum, auto

class GestureSlot(IntEnum):
    AttackAndReload = 0
    Grenade = 1
    Jump = 2
    Swim = 3
    Flinch = 4
    VCD = 5
    Custom = 6

    COUNT = auto()

class GestureSlotData:

    def __init__(self):
        self.gestureSlot = -1
        self.activity = Activity.Invalid
        self.autoKill = False
        self.active = False
        self.layerIndex = -1

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
        self.gestureSlots = []

    def initGestureSlots(self):
        self.gestureSlots = []

        self.player.seqPlayer.setNumLayers(GestureSlot.COUNT)
        for i in range(GestureSlot.COUNT):
            data = GestureSlotData()
            data.gestureSlot = i
            data.layerIndex = i
            self.gestureSlots.append(data)
            self.resetGestureSlot(i)

    def resetGestureSlots(self):
        for i in range(len(self.gestureSlots)):
            self.resetGestureSlot(i)

    def isGestureSlotActive(self, i):
        return self.gestureSlots[i].active

    def isGestureSlotPlaying(self, slot, activity):
        if not self.isGestureSlotActive(slot):
            return False

        return (self.gestureSlots[slot].activity == activity)

    def restartGesture(self, slot, activity, autoKill = True):
        if not self.isGestureSlotPlaying(slot, activity):
            act = self.translateActivity(activity)
            self.addGestureToSlot(slot, act, autoKill)
            return

        # Reset the cycle
        self.player.seqPlayer.resetLayer(slot, activity,
            self.player.seqPlayer.getLayerSequence(slot), autoKill)

    def addGestureToSlot(self, slot, activity, autoKill = True):
        if not self.player:
            return

        if self.gestureSlots[slot].layerIndex == -1:
            return

        sequence = self.player.getSequenceForActivity(activity)

        self.gestureSlots[slot].gestureSlot = slot
        self.gestureSlots[slot].activity = activity
        self.gestureSlots[slot].autoKill = autoKill
        self.gestureSlots[slot].active = True
        self.player.seqPlayer.resetLayer(slot, activity, sequence, autoKill)

    def resetGestureSlot(self, i):
        assert i >= 0 and i < len(self.gestureSlots)
        gestureSlot = self.gestureSlots[i]
        gestureSlot.gestureSlot = -1
        gestureSlot.activity = Activity.Invalid
        gestureSlot.autoKill = False
        gestureSlot.active = False
        self.player.seqPlayer.setLayerOrder(i, 15)

    def computeGestureSequence(self):
        for i in range(len(self.gestureSlots)):
            if not self.gestureSlots[i].active:
                continue
            self.updateGestureLayer(i)

    def updateGestureLayer(self, slot):
        if not self.player:
            return

        # TODO: Client-side

        gesture = self.gestureSlots[slot]
        if gesture.activity != Activity.Invalid and self.player.seqPlayer.getLayerActivity(slot) == Activity.Invalid:
            self.resetGestureSlot(slot)

    def doAnimationEvent(self, event, data):
        if event == PlayerAnimEvent.AttackPrimary:
            # Weapon primary fire.
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand)
        elif event == PlayerAnimEvent.AttackSecondary:
            # Weapon secondary fire.
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Attack_Stand)
        elif event == PlayerAnimEvent.AttackGrenade:
            # Grenade throw.
            pass
        elif event == PlayerAnimEvent.Reload:
            # TODO: crouching, swimming
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Reload_Stand)
        elif event == PlayerAnimEvent.ReloadLoop:
            # TODO: crouching, swimming
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Reload_Stand_Loop)
        elif event == PlayerAnimEvent.ReloadEnd:
            # TODO: crouching, swimming
            self.restartGesture(GestureSlot.AttackAndReload, Activity.Reload_Stand_End)

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
        yawParam = self.player.getPoseParameter("look_yaw")
        yawParam.setValue(-aimYaw / 45)
        self.player.lookYaw = yawParam.getValue()
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

        if self.player.activeWeapon != -1:
            wpn = base.net.doId2do.get(self.player.weapons[self.player.activeWeapon])
            if wpn:
                translateActivity = wpn.translateActivity(translateActivity)

        return translateActivity

    def calcMainActivity(self):
        ideal = Activity.Stand

        if abs(self.vel[0]) >= 0.1 or abs(self.vel[1]) >= 0.1:
            ideal = Activity.Run

        return ideal

    def computeMainSequence(self):
        idealActivity = self.calcMainActivity()

        # Store our current activity
        self.currentMainSequenceActivity = idealActivity

        if self.specificMainSequence >= 0:
            if self.player.getCurrSequence() != self.specificMainSequence:
                self.player.resetSequence(self.specificMainSequence)
                return

            if not self.player.isCurrentSequenceFinished():
                return

            self.specificMainSequence = -1
            self.restartMainSequence()

        animDesired = self.player.getSequenceForActivity(self.translateActivity(idealActivity))
        if self.player.getSequenceActivity(self.player.getCurrSequence()) == self.player.getSequenceActivity(animDesired):
            return

        if animDesired < 0:
            animDesired = 0

        self.player.resetSequence(animDesired)

    def update(self):
        pitchParam = self.player.getPoseParameter("look_pitch")
        #yawParam = self.player.getPoseParameter("look_yaw")
        moveXParam = self.player.getPoseParameter("move_x")
        moveYParam = self.player.getPoseParameter("move_y")

        self.vel = -self.player.getVelocity()
        vel = self.vel

        self.eyeYaw = self.angleNormalize(self.player.viewAngles[0])
        self.eyePitch = self.angleNormalize(self.player.viewAngles[1])

        self.computeMainSequence()
        self.computeGestureSequence()

        self.computeAimPoseParam()

        pitchParam.setValue(self.eyePitch / 90)
        self.player.lookPitch = pitchParam.getValue()

        forwardSpeed = BaseSpeed * self.player.classInfo.ForwardFactor
        backwardSpeed = BaseSpeed * self.player.classInfo.BackwardFactor
        moveXParam.setValue(vel[0] / forwardSpeed)
        moveYParam.setValue(vel[1] / forwardSpeed if vel[1] > 0 else vel[1] / backwardSpeed)

        self.player.moveX = moveXParam.getValue()
        self.player.moveY = moveYParam.getValue()


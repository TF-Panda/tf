from panda3d.core import *
from panda3d.pphysics import *

from .MovementVars import *
from .MoveType import MoveType

from tf.player.InputButtons import InputFlag
from tf.player.PlayerAnimEvent import PlayerAnimEvent

import math

def simpleSpline(self, val):
    valueSquared = val * val
    return (3 * valueSquared - 2 * valueSquared * val)

class GameMovement:

    def __init__(self):
        self.speedCropped = False
        self.player = None
        self.mv = None
        self.oldWaterLevel = 0
        self.forward = Vec3(0)
        self.up = Vec3(0)
        self.right = Vec3(0)

    def isControllerOnGround(self):
        """
        Returns true if the player is on the ground as of the last move.
        """
        return (self.player.controller.getCollisionFlags() & PhysController.CFDown) != 0

    def processMovement(self, player, moveData):
        storeDeltaTime = globalClock.getDt()
        self.speedCropped = False
        self.player = player
        self.mv = moveData
        self.mv.maxSpeed = sv_maxspeed.getValue()
        self.mv.onGround = self.isControllerOnGround()
        #if IS_CLIENT:
        #    print("Start move, on ground?", self.mv.onGround)
        ##    print("buttons", self.mv.buttons)
        #    print("old buttons", self.mv.oldButtons)

        self.playerMove()
        self.finishMove()

        globalClock.setDt(storeDeltaTime)
        base.deltaTime = storeDeltaTime

        #self.player.velocity = self.mv.velocity

        self.player = None

    def finishMove(self):
        pass

    def calcRoll(self, angles, velocity, rollAngle, rollSpeed):
        q = Quat()
        q.setHpr(angles)

        forward = q.getForward()
        right = q.getRight()
        up = q.getUp()

        side = velocity.dot(right)
        sign = -1 if side < 0 else 1
        side = abs(side)
        value = rollAngle
        if side < rollSpeed:
            side = side * value / rollSpeed
        else:
            side = value

        return side * side

    def decayPunchAngle(self):
        if self.player.punchAngle.lengthSquared() > 0.001 or self.player.punchAngleVel.lengthSquared() > 0.001:
            self.player.punchAngle += self.player.punchAngleVel * globalClock.getFrameTime()
            damping = 1 - (PUNCH_DAMPING * globalClock.getFrameTime())
            if damping < 0:
                damping = 0
            self.player.punchAngleVel *= damping
            springForceMagnitude = PUNCH_SPRING_CONSTANT * globalClock.getFrameTime()
            springForceMagnitude = max(0, min(2, springForceMagnitude))
            self.player.punchAngleVel -= self.player.punchAngle * springForceMagnitude
            # Don't wrap around.
            self.player.punchAngle[0] = max(-179, min(179, self.player.punchAngle[0]))
            self.player.punchAngle[1] = max(-89, min(89, self.player.punchAngle[1]))
            self.player.punchAngle[2] = max(-89, min(89, self.player.punchAngle[2]))
        else:
            self.player.punchAngle.set(0, 0, 0)
            self.player.punchAngleVel.set(0, 0, 0)

    def checkParameters(self):
        if self.player.moveType not in [MoveType.Isometric, MoveType.NoClip, MoveType.Observer]:
            spd = (self.mv.forwardMove * self.mv.forwardMove) + \
                  (self.mv.sideMove * self.mv.sideMove) + \
                  (self.mv.upMove * self.mv.upMove)
            maxspeed = self.mv.clientMaxSpeed
            if maxspeed != 0.0:
                self.mv.maxSpeed = min(maxspeed, self.mv.maxSpeed)

            # Slow down by the speed factor
            speedFactor = 1.0

            self.mv.maxSpeed *= speedFactor

            if (spd != 0.0) and (spd > self.mv.maxSpeed*self.mv.maxSpeed):
                ratio = self.mv.maxSpeed / math.sqrt(spd)
                self.mv.forwardMove *= ratio
                self.mv.sideMove *= ratio
                self.mv.upMove *= ratio

        self.decayPunchAngle()

        if not self.player.isDead():
            angle = Vec3(self.mv.angles)
            angle += self.player.punchAngle

            # Now adjust roll angle
            if self.player.moveType not in [MoveType.Isometric, MoveType.NoClip]:
                self.mv.angles[2] = self.calcRoll(angle, self.mv.velocity, sv_rollangle.getValue(), sv_rollspeed.getValue())
            else:
                self.mv.angles[2] = 0.0
            self.mv.angles[1] = angle[1]
            self.mv.angles[0] = angle[0]
        else:
            self.mv.angles = self.mv.oldAngles

        if self.player.isDead():
            pass

        # Adjust client view angles to match values used on server
        if self.mv.angles[0] > 180.0:
            self.mv.angles[0] -= 360

    def reduceTimers(self):
        frameMSec = globalClock.getDt() * 1000.0

        if self.player.duckTime > 0:
            self.player.duckTime -= frameMSec
            if self.player.duckTime < 0:
                self.player.duckTime = 0
        if self.player.duckJumpTime > 0:
            self.player.duckJumpTime -= frameMSec
            if self.player.duckJumpTime < 0:
                self.player.duckJumpTime = 0
        if self.player.jumpTime > 0:
            self.player.jumpTime -= frameMSec
            if self.player.jumpTime < 0:
                self.player.jumpTime = 0
        if self.player.swimSoundTime > 0:
            self.player.swimSoundTime -= frameMSec
            if self.player.swimSoundTime < 0:
                self.player.swimSoundTime = 0

    def setDuckedEyeOffset(self, offset):
        # FIXME
        pass

    def duck(self):
        """
        See if duck button is pressed and do the appropriate things.
        """
        buttonsChanged = (self.mv.oldButtons ^ self.mv.buttons)
        buttonsPressed = buttonsChanged & self.mv.buttons
        buttonsReleased = buttonsChanged & self.mv.oldButtons

        # Check to see if we are in the air.

    def updateDuckJumpEyeOffset(self):
        if self.player.duckJumpTime != 0:
            duckMs = max(0.0, GAMEMOVEMENT_DUCK_TIME - float(self.player.duckJumpTime))
            duckSec = duckMs / GAMEMOVEMENT_DUCK_TIME
            if duckSec > TIME_TO_UNDUCK:
                self.player.duckJumpTime = 0.0
                self.setDuckedEyeOffset(0)
            else:
                duckFraction = simpleSpline(1.0 - (duckSec / TIME_TO_UNDUCK))
                self.setDuckedEyeOffset(duckFraction)

    def playerMove(self):
        self.checkParameters()
        self.mv.outWishVel.set(0, 0, 0)
        self.mv.outJumpVel.set(0, 0, 0)

        self.reduceTimers()

        q = Quat()
        q.setHpr(self.mv.viewAngles)
        self.forward = q.getForward()
        self.right = q.getRight()
        self.up = q.getUp()

        self.oldWaterLevel = self.player.waterLevel

        self.updateDuckJumpEyeOffset()
        self.duck()

        # Handle movement modes.
        if self.player.moveType == MoveType.Walk:
            self.fullWalkMove()
        else:
            assert False

    def checkVelocity(self):
        for i in range(3):
            if math.isnan(self.mv.velocity[i]):
                self.mv.velocity[i] = 0

            if math.isnan(self.mv.origin[i]):
                self.mv.origin[i] = 0

            if self.mv.velocity[i] > sv_maxvelocity.getValue():
                self.mv.velocity[i] = sv_maxvelocity.getValue()
            elif self.mv.velocity[i] < -sv_maxvelocity.getValue():
                self.mv.velocity[i] = -sv_maxvelocity.getValue()

    def startGravity(self):
        if self.player.gravity:
            entGravity = self.player.gravity
        else:
            entGravity = 1.0
        self.mv.velocity[2] -= (entGravity * sv_gravity.getValue() * 0.5 * globalClock.getDt())
        self.mv.velocity[2] += self.player.baseVelocity[2] * globalClock.getDt()

        temp = Vec3(self.player.baseVelocity)
        temp[2] = 0
        self.player.baseVelocity = temp

        self.checkVelocity()

    def canAccelerate(self):
        return True

    def accelerate(self, wishdir, wishspeed, accel):
        if not self.canAccelerate():
            return

        # See if we are changing direction a bit.
        currentspeed = self.mv.velocity.dot(wishdir)
        # Reduce wishspeed by the amount of veer.
        addspeed = wishspeed - currentspeed

        # If not going to add any speed, done.
        if addspeed <= 0:
            return

        # Determine amount of acceleration
        accelspeed = accel * globalClock.getDt() * wishspeed * self.player.surfaceFriction

        # Cap at addspeed
        if accelspeed > addspeed:
            accelspeed = addspeed

        self.mv.velocity += wishdir * accelspeed

    def walkMove(self):
        q = Quat()
        # Determine forward vector from yaw only.
        q.setHpr((self.mv.viewAngles[0], 0, 0))
        forward = q.getForward()
        up = q.getUp()
        right = q.getRight()

        fmove = self.mv.forwardMove
        smove = self.mv.sideMove

        wishvel = Vec3(0)

        if True:
            if forward[2] != 0:
                forward[2] = 0
                forward.normalize()

            if right[2] != 0:
                right[2] = 0
                right.normalize()

        wishvel = (forward*fmove) + (right*smove)
        wishvel[2] = 0
        wishdir = Vec3(wishvel)
        wishspeed = wishdir.length()
        wishdir.normalize()

        # Clamp to server defined min/max.
        if (wishspeed != 0.0) and (wishspeed > self.mv.maxSpeed):
            wishvel *= self.mv.maxSpeed / wishspeed
            wishspeed = self.mv.maxSpeed

        self.mv.velocity[2] = 0
        self.accelerate(wishdir, wishspeed, sv_accelerate.getValue())
        self.mv.velocity[2] = 0

        # Add in any base velocity to the current velocity
        self.mv.velocity += self.player.baseVelocity
        spd = self.mv.velocity.length()

        if spd < 1.0:
            self.mv.velocity.set(0, 0, 0)
            # Now pull the base velocity back out.  Base velocity is set if you are on a moving object.
            self.mv.velocity -= self.player.baseVelocity
            return

        vel = self.mv.velocity * globalClock.getDt()
        vel[2] = -2 # To detect if we're on the ground.

        self.mv.oldOrigin = self.mv.origin
        flags = self.player.controller.move(globalClock.getDt(), vel, 0.1)
        self.mv.origin = self.player.controller.getFootPosition()

        self.mv.outWishVel += wishdir * wishspeed

        # This is the new, clipped velocity.
        self.mv.velocity = (self.mv.origin - self.mv.oldOrigin) / globalClock.getDt()

        # Pull the base velocity back out
        self.mv.velocity -= self.player.baseVelocity

    def airAccelerate(self, wishdir, wishspeed, accel):
        wishspd = wishspeed

        if self.player.isDead():
            # ???
            return

        # TODO: water jump time

        # Cap speed
        if wishspd > 30:
            wishspd = 30

        # Determine veer amount
        currentspeed = self.mv.velocity.dot(wishdir)
        # See how much to add
        addspeed = wishspd - currentspeed

        # If not adding any, done.
        if addspeed <= 0:
            return

        # Determine acceleration speed after acceleration
        accelspeed = accel * wishspeed * globalClock.getDt() * self.player.surfaceFriction

        # Cap it
        if (accelspeed > addspeed):
            accelspeed = addspeed

        # Adjust move vel
        self.mv.velocity += wishdir * accelspeed
        self.mv.outWishVel += wishdir * accelspeed

    def airMove(self):
        q = Quat()
        q.setHpr(self.mv.viewAngles)
        forward = q.getForward()
        up = q.getUp()
        right = q.getRight()

        fmove = self.mv.forwardMove
        smove = self.mv.sideMove

        # Zero out z components of movement vectors
        forward[2] = 0
        right[2] = 0
        forward.normalize()
        right.normalize()

        wishvel = (forward * fmove) + (right * smove)
        wishvel[2] = 0

        wishdir = Vec3(wishvel)
        wishspeed = wishdir.length()
        wishdir.normalize()

        # Clamp to server defined max speed
        if wishspeed != 0 and (wishspeed > self.mv.maxSpeed):
            wishvel *= self.mv.maxSpeed / wishspeed
            wishspeed = self.mv.maxSpeed

        self.airAccelerate(wishdir, wishspeed, sv_airaccelerate.getValue())

        # Add in any base velocity to the current velo.
        self.mv.velocity += self.player.baseVelocity

        self.mv.oldOrigin = self.mv.origin
        flags = self.player.controller.move(globalClock.getDt(), self.mv.velocity * globalClock.getDt(), 0.1)
        self.mv.origin = self.player.controller.getFootPosition()

        self.mv.outWishVel += wishdir * wishspeed

        # This is the new, clipped velocity.
        self.mv.velocity = (self.mv.origin - self.mv.oldOrigin) / globalClock.getDt()

        # Pull the base velocity back out
        self.mv.velocity -= self.player.baseVelocity

    def friction(self):
        # Calculate speed
        speed = self.mv.velocity.length()

        # If too slow, return
        if speed < 0.1:
            return

        drop = 0

        # Apply ground friction
        if self.mv.onGround:
            friction = sv_friction.getValue() * self.player.surfaceFriction
            control = sv_stopspeed.getValue() if (speed < sv_stopspeed.getValue()) else speed

            # Add the amount to the drop amount
            drop += control * friction * globalClock.getDt()

            #print("Drop is", drop)

        # SCale the velocity
        newspeed = speed - drop
        if newspeed < 0:
            newspeed = 0

        if newspeed != speed:
            newspeed /= speed
            self.mv.velocity *= newspeed

        self.mv.outWishVel -= self.mv.velocity * (1.0 - newspeed)

    def finishGravity(self):
        if self.player.gravity:
            entGravity = self.player.gravity
        else:
            entGravity = 1.0

        self.mv.velocity[2] -= (entGravity * sv_gravity.getValue() * globalClock.getDt() * 0.5)

        self.checkVelocity()

    def checkWater(self):
        return False

    def checkJumpButton(self):
        """
        Performs a jump.
        """

        if self.player.isDead():
            # ???
            self.mv.oldButtons &= ~InputFlag.Jump
            return False

        # TODO: See if we are water jumping.

        if not self.mv.onGround:
            self.mv.oldButtons &= ~InputFlag.Jump
            return False # in air, so no effect

        if self.mv.oldButtons & InputFlag.Jump:
            # Don't pogo stick!
            return False

        # TODO: Cannot jump while in the unduck transition.
        # TODO: Still updating eye position.

        #if IS_CLIENT:
        #    print("Jumping")

        # Start jump animation.
        self.player.doAnimationEvent(PlayerAnimEvent.Jump)

        # In the air now.
        self.mv.onGround = False

        groundFactor = 1.0

        #mul = math.sqrt(2 * sv_gravity.getValue() * GAMEMOVEMENT_JUMP_HEIGHT)
        assert (sv_gravity.getValue() == 800)
        mul = 268.3281572999747 * groundFactor

        # Accelerate upward
        # TODO: IF we are ducking
        startZ = self.mv.velocity[2]
        self.mv.velocity[2] += groundFactor * mul

        self.finishGravity()

        self.mv.outJumpVel[2] += self.mv.velocity[2] - startZ
        self.mv.outStepHeight += 0.15

        # Flag that we jumped
        self.mv.oldButtons &= ~InputFlag.Jump

        return True

    #def checkFalling(self):


    def fullWalkMove(self):
        if (not self.checkWater()):
            self.startGravity()

        # Was jump button pressed?
        if (self.mv.buttons & InputFlag.Jump):
            self.checkJumpButton()
        else:
            self.mv.oldButtons &= ~InputFlag.Jump

        if self.mv.onGround:
            # Apply friction if on ground.
            self.mv.velocity[2] = 0.0
            self.friction()

        # Make sure velocity is valid.
        self.checkVelocity()

        # Do the move.  This will clip our velocity and tell us if we are on
        # the ground.
        if self.mv.onGround:
            self.walkMove()
        else:
            self.airMove()

        self.mv.onGround = self.isControllerOnGround()

        self.checkVelocity()

        if not self.checkWater():
            self.finishGravity()

        if self.mv.onGround:
            self.mv.velocity[2] = 0.0

        #self.checkFalling()

g_game_movement = GameMovement()

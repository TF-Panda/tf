# Code referenced exactly from gamemovement.cpp/tf_gamemovement.cpp.
# It's horrible, want to clean it up eventually.

from panda3d.core import *
from panda3d.pphysics import *

from .MovementVars import *
from .MoveType import MoveType

from tf.player.InputButtons import InputFlag
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.player.TFClass import Class
from tf.tfbase import TFFilters
from tf.tfbase.TFGlobals import VEC_HULL_MAX, VEC_HULL_MIN, VEC_DUCK_HULL_MIN, VEC_DUCK_HULL_MAX, VEC_DUCK_VIEW

import math

def simpleSpline(val):
    valueSquared = val * val
    return (3 * valueSquared - 2 * valueSquared * val)

PUNCH_DAMPING = 9.0
PUNCH_SPRING_CONSTANT = 65.0

PLAYER_FATAL_FALL_SPEED = 1024
PLAYER_MAX_SAFE_FALL_SPEED = 580
PLAYER_LAND_ON_FLOATING_OBJECT = 200
PLAYER_MIN_BOUNCE_SPEED = 200
PLAYER_FALL_PUNCH_THRESHOLD = 350
DAMAGE_FOR_FALL_SPEED = 100.0 / (PLAYER_FATAL_FALL_SPEED - PLAYER_MAX_SAFE_FALL_SPEED)

class GameMovement:

    def __init__(self):
        self.speedCropped = False
        self.player = None
        self.mv = None
        self.oldWaterLevel = 0
        self.forward = Vec3(0)
        self.up = Vec3(0)
        self.right = Vec3(0)

    def getMovementFilter(self):
        return TFFilters.TFQueryFilter(self.player, [TFFilters.ignoreTeammateBuildings_nonBuilder])

    def processMovement(self, player, moveData):
        #storeDeltaTime = base.clockMgr.getDeltaTime()
        self.speedCropped = False
        self.player = player
        self.mv = moveData
        #self.mv.maxSpeed = sv_maxspeed.value
        self.mv.maxSpeed = self.player.maxSpeed
        #self.mv.onGround = self.isControllerOnGround()
        #if self.mv.onGround:
        #    self.player.airDashing = False
        #if IS_CLIENT:
        #    print("Start move, on ground?", self.mv.onGround)
        ##    print("buttons", self.mv.buttons)
        #    print("old buttons", self.mv.oldButtons)

        self.playerMove()
        self.finishMove()

        #base.clockMgr.getDeltaTime() = storeDeltaTime
        #base.deltaTime = storeDeltaTime

        #self.player.velocity = self.mv.velocity

        self.player = None

    def finishMove(self):
        self.mv.oldButtons = self.mv.buttons

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
            dt = base.clockMgr.getDeltaTime()
            self.player.punchAngle += self.player.punchAngleVel * dt
            damping = 1 - (PUNCH_DAMPING * dt)
            if damping < 0:
                damping = 0
            self.player.punchAngleVel *= damping
            springForceMagnitude = PUNCH_SPRING_CONSTANT * dt
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
                self.mv.angles[2] = self.calcRoll(angle, self.mv.velocity, sv_rollangle.value, sv_rollspeed.value)
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
        frameMSec = base.clockMgr.getDeltaTime() * 1000.0

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
        #duckHullMin = self.getPlayerHullMins(True)
        #standHullMin = self.getPlayerHullMins(False)

        #more = duckHullMin.z - standHullMin.z

        duckViewOffset = self.getPlayerViewOffset(True)
        standViewOffset = self.getPlayerViewOffset(False)
        tmp = Vec3(self.player.viewOffset)
        tmp.z = (duckViewOffset.z * offset) + (standViewOffset.z * (1 - offset))
        #print(tmp)
        self.player.viewOffset = tmp

    def handleDuckSpeedCrop(self):
        if not self.speedCropped and self.player.duckFlag and self.mv.onGround:
            frac = 0.333333333
            self.mv.forwardMove *= frac
            self.mv.sideMove *= frac
            self.mv.upMove *= frac
            self.speedCropped = True

    def canUnDuckJump(self):
        end = Vec3(self.mv.origin)
        end.z -= 36.0
        tr = self.tracePlayerHull(self.mv.origin, end)
        if tr['frac'] < 1.0:
            end.z = mv.origin.z + (-36.0 * tr['frac'])

            # Test a normal hull.
            wasDucked = self.player.ducked
            self.player.ducked = False
            trUp = self.tracePlayerHull(end, end)
            self.player.ducked = wasDucked
            if not tr['startsolid']:
                return (True, tr)

        return (False, tr)

    def finishUnDuckJump(self, tr):
        newOrigin = Vec3(self.mv.origin)

        # Up for uncrouching.
        hullSizeNormal = VEC_HULL_MAX - VEC_HULL_MIN
        hullSizeCrouch = VEC_DUCK_HULL_MAX - VEC_DUCK_HULL_MIN
        viewDelta = (hullSizeNormal - hullSizeCrouch)

        deltaZ = viewDelta.z
        viewDelta.z *= tr['frac']
        deltaZ -= viewDelta.z

        self.player.duckFlag = False
        self.player.ducked = False
        self.player.ducking = False
        self.player.inDuckJump = False
        self.player.duckTime = 0.0
        self.player.duckJumpTime = 0.0
        self.player.jumpTime = 0.0

        viewOffset = self.getPlayerViewOffset(False)
        viewOffset.z -= deltaZ
        self.player.viewOffset = viewOffset

        newOrigin -= viewDelta
        self.mv.origin = newOrigin
        #self.mv.oldOrigin = Vec3(self.mv.origin)

    def canUnDuck(self):
        newOrigin = Vec3(self.mv.origin)

        if self.mv.onGround:
            newOrigin.z += VEC_HULL_MAX.z - VEC_DUCK_HULL_MAX.z
            #pass
            #for i in range(3):
            #    newOrigin[i] += (VEC_DUCK_HULL_MIN[i] - VEC_HULL_MIN[i])
        else:
            # If in air letting go of crouch, make sure we can offset origin
            # to make up for uncrouching.
            hullSizeNormal = VEC_HULL_MAX - VEC_HULL_MIN
            hullSizeCrouch = VEC_DUCK_HULL_MAX - VEC_DUCK_HULL_MIN
            viewDelta = (hullSizeNormal - hullSizeCrouch)
            viewDelta = -viewDelta
            newOrigin += viewDelta

        wasDucked = self.player.ducked
        self.player.ducked = True
        tr = self.tracePlayerHull(newOrigin, newOrigin)
        self.player.ducked = wasDucked
        if tr['startsolid'] or tr['frac'] != 1.0:
            return False

        return True

    def finishUnDuck(self):
        newOrigin = Vec3(self.mv.origin)

        if self.mv.onGround:
            pass
            #for i in range(3):
            #    newOrigin[i] += (VEC_DUCK_HULL_MIN[i] - VEC_HULL_MIN[i])
        else:
            # If in air letting go of crouch, make sure we can offset origin
            # to make up for uncrouching.
            hullSizeNormal = VEC_HULL_MAX - VEC_HULL_MIN
            hullSizeCrouch = VEC_DUCK_HULL_MAX - VEC_DUCK_HULL_MIN
            viewDelta = (hullSizeNormal - hullSizeCrouch)
            viewDelta = -viewDelta
            newOrigin += viewDelta

        self.player.ducked = False
        self.player.duckFlag = False
        self.player.ducking = False
        self.player.inDuckJump = False
        self.player.viewOffset = self.getPlayerViewOffset(False)
        self.player.duckTime = 0.0

        self.mv.origin = newOrigin
        #self.mv.oldOrigin = Vec3(self.mv.origin)

    def duck(self):
        """
        See if duck button is pressed and do the appropriate things.
        """
        buttonsChanged = (self.mv.oldButtons ^ self.mv.buttons)
        buttonsPressed = buttonsChanged & self.mv.buttons
        buttonsReleased = buttonsChanged & self.mv.oldButtons

        # Check to see if we are in the air.
        inAir = not self.mv.onGround
        inDuck = self.player.duckFlag
        duckJump = self.player.jumpTime > 0.0
        duckJumpTime = self.player.duckJumpTime > 0.0

        if self.mv.buttons & InputFlag.Crouch:
            self.mv.oldButtons |= InputFlag.Crouch
        else:
            self.mv.oldButtons &= ~InputFlag.Crouch

        if self.player.isDead():
            return

        # Slow down ducked players.
        self.handleDuckSpeedCrop()

        # If the player is holding down the duck button, the player is in the duck transition, ducking, or duck-jumping.
        if (self.mv.buttons & InputFlag.Crouch) or self.player.ducking or inDuck or duckJump:
            # DUCK
            if (self.mv.buttons & InputFlag.Crouch) or duckJump:
                # Have the duck button pressed, but the player currently isn't in the duck position.
                if (buttonsPressed & InputFlag.Crouch) and not inDuck and not duckJump and not duckJumpTime:
                    self.player.duckTime = GAMEMOVEMENT_DUCK_TIME
                    self.player.ducking = True

                # The player is in the duck transition and not duck-jumping.
                if self.player.ducking and not duckJump and not duckJumpTime:
                    duckMs = max(0.0, GAMEMOVEMENT_DUCK_TIME - self.player.duckTime)
                    duckSecs = duckMs * 0.001

                    # Finish duck transition when time is over, in "duck", in air.
                    if (duckSecs > TIME_TO_DUCK) or inDuck or inAir:
                        self.finishDuck()
                    else:
                        # Calc parametric time
                        duckFraction = simpleSpline(duckSecs / TIME_TO_DUCK)
                        self.setDuckedEyeOffset(duckFraction)

                if duckJump:
                    if not inDuck:
                        self.startUnDuckJump()
                    else:
                        # Check for a crouch override.
                        if not (self.mv.buttons & InputFlag.Crouch):
                            ret, tr = self.canUnDuckJump()
                            if ret:
                                self.finishUnDuckJump(tr)
                                self.player.duckJumpTime = (GAMEMOVEMENT_TIME_TO_UNDUCK * (1.0 - tr['frac'])) + GAMEMOVEMENT_TIME_TO_UNDUCK_INV
            else:
                # UNDUCK (or attempt to...)
                if self.player.inDuckJump:
                    if not (self.mv.buttons & InputFlag.Crouch):
                        ret, tr = self.canUnDuckJump()
                        if ret:
                            self.finishUnDuckJump(tr)
                            if tr['frac'] < 1.0:
                                self.player.duckJumpTime = (GAMEMOVEMENT_TIME_TO_UNDUCK * (1.0 - tr['frac'])) + GAMEMOVEMENT_TIME_TO_UNDUCK_INV
                    else:
                        self.player.inDuckJump = False

                if duckJumpTime:
                    return

                # Try to unduck unless automovement is not allowed.
                if self.player.allowAutoMovement or inAir or self.player.ducking:
                    # We released the duck button, we aren't in "duck" and we are not in the air --
                    # start unduck transition.
                    if buttonsReleased & InputFlag.Crouch:
                        if inDuck and not duckJump:
                            self.player.duckTime = GAMEMOVEMENT_DUCK_TIME
                        elif self.player.ducking and not self.player.ducked:
                            # Invert time if release before fully ducked.
                            unduckMS = 1000.0 * TIME_TO_UNDUCK
                            duckMS = 1000.0 * TIME_TO_DUCK
                            elapsedMS = GAMEMOVEMENT_DUCK_TIME - self.player.duckTime
                            fracDucked = elapsedMS / duckMS
                            remainingUnduckMS = fracDucked * unduckMS
                            self.player.duckTime = GAMEMOVEMENT_DUCK_TIME - unduckMS + remainingUnduckMS


                    # Check to see if we are capable of unducking.
                    if self.canUnDuck():
                        # or unducking.
                        if self.player.ducking or self.player.ducked:
                            duckMS = max(0.0, GAMEMOVEMENT_DUCK_TIME - self.player.duckTime)
                            duckSec = duckMS * 0.001

                            # Finish ducking immediately if duck time is over or not on ground.
                            if duckSec > TIME_TO_UNDUCK or (inAir and not duckJump):
                                self.finishUnDuck()
                            else:
                                # Calc parametric time.
                                duckFrac = simpleSpline(1.0 - (duckSec / TIME_TO_UNDUCK))
                                self.setDuckedEyeOffset(duckFrac)
                                self.player.ducking = True

                    else:
                        # Still under something where we can't unduck, so make sure we reset this timer
                        # so that we'll unduck once we exit the tunnel, etc.
                        if self.player.duckTime != GAMEMOVEMENT_DUCK_TIME:
                            self.setDuckedEyeOffset(1.0)
                            self.player.duckTime = GAMEMOVEMENT_DUCK_TIME
                            self.player.ducked = True
                            self.player.ducking = False

    def startUnDuckJump(self):
        self.player.ducking = True
        self.player.ducked = True
        self.player.ducking = False

        self.player.viewOffset = self.getPlayerViewOffset(True)

        hullSizeNormal = VEC_HULL_MAX - VEC_HULL_MIN
        hullSizeCrouch = VEC_DUCK_HULL_MAX - VEC_DUCK_HULL_MIN
        viewDelta = (hullSizeNormal - hullSizeCrouch)
        out = self.mv.origin + viewDelta
        self.mv.origin = out

        self.fixPlayerCrouchStuck(True)

    def getPlayerViewOffset(self, ducked):
        return Vec3(VEC_DUCK_VIEW) if ducked else self.player.getClassViewOffset()

    def getPlayerHullMins(self, ducked):
        return Vec3(VEC_DUCK_HULL_MIN) if ducked else Vec3(VEC_HULL_MIN)

    def getPlayerHullMaxs(self, ducked):
        return Vec3(VEC_DUCK_HULL_MAX) if ducked else Vec3(VEC_HULL_MAX)

    def tracePlayerHull(self, start, end):
        mask = self.player.getPlayerCollideMask()
        filter = TFFilters.TFQueryFilter(self.player, [TFFilters.ignoreTeammateBuildings_nonBuilder])
        mins = self.getPlayerHullMins(self.player.ducked)
        maxs = self.getPlayerHullMaxs(self.player.ducked)
        tr = TFFilters.traceBox(start, end, mins, maxs, mask, filter)
        return tr

    def testPlayerPosition(self, pos):
        intoMask = self.player.getPlayerCollideMask()
        tr = TFFilters.traceBox(pos, pos, self.getPlayerHullMins(self.player.ducked), self.getPlayerHullMaxs(self.player.ducked),
                                intoMask, TFFilters.TFQueryFilter(self.player, [TFFilters.ignoreTeammateBuildings_nonBuilder]))
        if tr['hit'] and tr['ent']:
            if tr['actor'].getFromCollideMask() & intoMask:
                return tr

        return None

    def finishDuck(self):
        self.player.duckFlag = True
        self.player.ducked = True
        self.player.ducking = False

        self.player.viewOffset = self.getPlayerViewOffset(True)

        if self.mv.onGround:
            pass
            #for i in range(3):
            #    self.mv.origin[i] -= (VEC_DUCK_HULL_MIN[i] - VEC_HULL_MIN[i])
        else:
            hullSizeNormal = VEC_HULL_MAX - VEC_HULL_MIN
            hullSizeCrouch = VEC_DUCK_HULL_MAX - VEC_DUCK_HULL_MIN
            viewDelta = (hullSizeNormal - hullSizeCrouch)
            out = self.mv.origin + viewDelta
            self.mv.origin = out

        self.fixPlayerCrouchStuck(True)

    def fixPlayerCrouchStuck(self, upward):
        tr = self.testPlayerPosition(self.mv.origin)
        if not tr:
            return

        direction = 1 if upward else 0

        test = Point3(self.mv.origin)
        for _ in range(36):
            self.mv.origin.z += direction
            tr = self.testPlayerPosition(self.mv.origin)
            if not tr:
                return

        self.mv.origin = test

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

        if self.mv.velocity.z > 250.0:
            self.mv.onGround = False

        self.oldWaterLevel = self.player.waterLevel

        if not self.mv.onGround:
            self.player.fallVelocity = -self.mv.velocity[2]

        self.player.updateStepSound(self.mv.origin, self.mv.velocity)

        self.updateDuckJumpEyeOffset()
        self.duck()

        # Handle movement modes.
        if self.player.moveType == MoveType.Walk:
            self.fullWalkMove()
        else:
            assert False

        # TODO: TF water interaction

    def checkVelocity(self):
        for i in range(3):
            #if math.isnan(self.mv.velocity[i]):
            #    self.mv.velocity[i] = 0

            #if math.isnan(self.mv.origin[i]):
            #    self.mv.origin[i] = 0

            if self.mv.velocity[i] > sv_maxvelocity.value:
                self.mv.velocity[i] = sv_maxvelocity.value
            elif self.mv.velocity[i] < -sv_maxvelocity.value:
                self.mv.velocity[i] = -sv_maxvelocity.value

    def startGravity(self):
        if self.player.gravity:
            entGravity = self.player.gravity
        else:
            entGravity = 1.0
        self.mv.velocity[2] -= (entGravity * sv_gravity.value * 0.5 * base.clockMgr.getDeltaTime())
        self.mv.velocity[2] += self.player.baseVelocity[2] * base.clockMgr.getDeltaTime()

        temp = Vec3(self.player.baseVelocity)
        temp[2] = 0
        self.player.baseVelocity = temp

        self.checkVelocity()

    def canAccelerate(self):
        # TODO: false if water jumping?
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
        accelspeed = accel * base.clockMgr.getDeltaTime() * wishspeed * self.player.surfaceFriction

        # Cap at addspeed
        if accelspeed > addspeed:
            accelspeed = addspeed

        self.mv.velocity += wishdir * accelspeed

    def walkMove(self):
        # Get movement direction, ignoring Z.
        forward = Vec3(self.forward)
        right = Vec3(self.right)
        forward.z = 0.0
        right.z = 0.0
        forward.normalize()
        right.normalize()

        fmove = self.mv.forwardMove
        smove = self.mv.sideMove

        wishDirection = Vec3(
            forward.x * fmove + right.x * smove,
            forward.y * fmove + right.y * smove,
            0
        )

        # Calculate the speed and direction of movement, then clamp the speed.
        wishSpeed = wishDirection.length()
        if wishSpeed > 0.0:
            wishDirection /= wishSpeed
        wishSpeed = max(0.0, min(self.mv.maxSpeed, wishSpeed))

        # Accelerate in the x/y plane.
        self.mv.velocity.z = 0.0
        self.accelerate(wishDirection, wishSpeed, sv_accelerate.value)

        # Clamp the players speed in x/y.
        newSpeed = self.mv.velocity.length()
        if newSpeed > self.mv.maxSpeed:
            scale = self.mv.maxSpeed / newSpeed
            self.mv.velocity.x *= scale
            self.mv.velocity.y *= scale

        # Now reduce their backwards speed to some percent of max,
        # if they are travelling backwards unless they are under some minimum,
        # to not penalize deployed snipers or heavies.
        tf_clamp_back_speed = 0.9
        tf_clamp_back_speed_min = 100
        if (tf_clamp_back_speed < 1.0 and self.mv.velocity.length() > tf_clamp_back_speed_min):
            dot = forward.dot(self.mv.velocity)

            # Are we moving backwards at all?
            if dot < 0:
                backMove = forward * dot
                rightMove = right * right.dot(self.mv.velocity)

                # Clamp the back move vector if it is faster than max.
                backSpeed = backMove.length()
                maxBackSpeed = (self.mv.maxSpeed * tf_clamp_back_speed)

                if backSpeed > maxBackSpeed:
                    backMove *= maxBackSpeed / backSpeed

                # Reassemble velocity.
                self.mv.velocity = backMove + rightMove

        # Add in any base velocity to the current velocity
        self.mv.velocity += self.player.baseVelocity

        spd = self.mv.velocity.length()
        #if spd < 1.0:
        #    self.mv.velocity.set(0, 0, 0)
        #    self.mv.velocity -= self.player.baseVelocity
        #    return

        vel = self.mv.velocity * base.clockMgr.getDeltaTime()
        vel[2] = -2 # To detect if we're on the ground.

        self.mv.oldOrigin = self.mv.origin
        filter = self.getMovementFilter()
        self.updateControllerSize()
        self.player.controller.foot_position = self.mv.origin
        flags = self.player.controller.move(base.clockMgr.getDeltaTime(), vel, 0.0,
            self.player.getPlayerCollideMask(), filter.filter)
        self.mv.origin = self.player.controller.foot_position

        self.mv.outWishVel += wishDirection * wishSpeed

        # This is the new, clipped velocity.
        self.mv.velocity = (self.mv.origin - self.mv.oldOrigin) / base.clockMgr.getDeltaTime()

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
        accelspeed = accel * wishspeed * base.clockMgr.getDeltaTime() * self.player.surfaceFriction

        # Cap it
        if (accelspeed > addspeed):
            accelspeed = addspeed

        # Adjust move vel
        self.mv.velocity += wishdir * accelspeed
        self.mv.outWishVel += wishdir * accelspeed

    def airMove(self):
        forward = Vec3(self.forward)
        up = Vec3(self.up)
        right = Vec3(self.right)

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

        self.airAccelerate(wishdir, wishspeed, sv_airaccelerate.value)

        # Add in any base velocity to the current velo.
        self.mv.velocity += self.player.baseVelocity

        self.mv.oldOrigin = self.mv.origin
        filter = self.getMovementFilter()
        self.updateControllerSize()
        self.player.controller.foot_position = self.mv.origin
        flags = self.player.controller.move(base.clockMgr.getDeltaTime(), self.mv.velocity * base.clockMgr.getDeltaTime(), 0.1,
            self.player.getPlayerCollideMask(), filter.filter)
        self.mv.origin = self.player.controller.foot_position

        self.mv.outWishVel += wishdir * wishspeed

        # This is the new, clipped velocity.
        self.mv.velocity = (self.mv.origin - self.mv.oldOrigin) / base.clockMgr.getDeltaTime()

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
            friction = sv_friction.value * self.player.surfaceFriction
            control = sv_stopspeed.value if (speed < sv_stopspeed.value) else speed

            # Add the amount to the drop amount
            drop += control * friction * base.clockMgr.getDeltaTime()

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

        self.mv.velocity[2] -= (entGravity * sv_gravity.value * base.clockMgr.getDeltaTime() * 0.5)

        self.checkVelocity()

    def checkWater(self):
        return False

    def checkJumpButton(self):
        """
        Performs a jump.
        """

        if self.player.isDead():
            return False

        # TODO: See if we are water jumping.

        # Cannot jump while aiming.
        if self.player.inCondition(self.player.CondAiming):
            return False

        isScout = self.player.tfClass == Class.Scout
        airDash = False
        onGround = bool(self.mv.onGround)

        # Cannot jump while ducked.
        if self.player.duckFlag:
            # Let a scout do it.
            allow = isScout and not onGround
            if not allow:
                return False

        # Cannot jump while in the unduck transition.
        if (self.player.ducking and self.player.duckFlag) or self.player.duckJumpTime > 0.0:
            return False

        if self.mv.oldButtons & InputFlag.Jump:
            # Don't pogo stick!
            return False

        # In air, so ignore jumps (unless you are a scout).
        if not onGround:
            if isScout and not self.player.airDashing:
                airDash = True
            else:
                self.mv.oldButtons |= InputFlag.Jump
                return False

        # Check for a scout air dash.
        if airDash:
            self.airDash()
            return True

        self.preventBunnyJumping()

        # Start jump animation.
        self.player.doAnimationEvent(PlayerAnimEvent.Jump)
        # Play footstep sound.
        self.player.playStepSound(self.mv.origin, 1.0, True)

        # In the air now.
        self.mv.onGround = False
        #print("jump at cmdnum", self.player.currentCommand.commandNumber)

        groundFactor = 1.0

        #mul = math.sqrt(2 * sv_gravity.value * GAMEMOVEMENT_JUMP_HEIGHT)
        assert (sv_gravity.value == 800)
        mul = 268.3281572999747 * groundFactor

        # Accelerate upward
        # TODO: IF we are ducking
        startZ = self.mv.velocity[2]

        if self.player.ducking or self.player.duckFlag:
            self.mv.velocity[2] = mul
        else:
            self.mv.velocity[2] += mul

        self.finishGravity()

        self.mv.outJumpVel[2] += self.mv.velocity[2] - startZ
        self.mv.outStepHeight += 0.15

        # Flag that we jumped
        self.mv.oldButtons |= InputFlag.Jump

        return True

    def airDash(self):
        """
        Does a Scout air dash.
        """

        assert(sv_gravity.value == 800)
        dashZ = 268.3281572999747

        # Get the wish direction.
        forward = Vec3(self.forward)
        forward[2] = 0.0
        right = Vec3(self.right)
        right[2] = 0.0
        forward.normalize()
        right.normalize()

        # Find the direction, velocity in the x/y plane.
        wishDirection = Vec3(
            forward.x * self.mv.forwardMove + right.x * self.mv.sideMove,
            forward.y * self.mv.forwardMove + right.y * self.mv.sideMove,
            0.0
        )

        # Update the velocity on the Scout.
        self.mv.velocity = wishDirection
        self.mv.velocity.z += dashZ

        self.player.airDashing = True

        self.player.doAnimationEvent(PlayerAnimEvent.DoubleJump)

    def preventBunnyJumping(self):
        # Speed at which bunny jumping is limited.
        maxScaledSpeed = 1.2 * self.mv.maxSpeed
        if maxScaledSpeed <= 0.0:
            return

        # Current player speed.
        spd = self.mv.velocity.length()
        if spd <= maxScaledSpeed:
            return

        # Apply this cropping friction to velocity.
        fraction = maxScaledSpeed / spd
        self.mv.velocity *= fraction

    def checkFalling(self):
        if self.mv.onGround and not self.player.isDead() and self.player.fallVelocity >= PLAYER_FALL_PUNCH_THRESHOLD:
            #alive = True
            vol = 0.5

            if False: # self.player.waterLevel > 0
                pass
            else:
                # They hit the ground.
                if self.player.fallVelocity > PLAYER_MAX_SAFE_FALL_SPEED:
                    #alive = self.player.playerFallingDamage()
                    if not IS_CLIENT:
                        self.player.playerFallingDamage()
                    vol = 1.0
                elif self.player.fallVelocity > PLAYER_MAX_SAFE_FALL_SPEED * 0.5:
                    vol = 0.85
                elif self.player.fallVelocity < PLAYER_MIN_BOUNCE_SPEED:
                    vol = 0.0

            self.playerRoughLandingEffects(vol)

        if self.mv.onGround:
            self.player.fallVelocity = 0.0

    def playerRoughLandingEffects(self, vol):
        if self.player.tfClass == Class.Scout:
            # Scouts don't play rumble unless they take damage.
            if vol < 1.0:
                vol = 0.0

        if vol == 0.0:
            return

        # Play ladning sound right awway.
        self.player.stepSoundTime = 400

        # Play step sound for current texture.
        self.player.playStepSound(self.mv.origin, vol, True)

        # Knock the screen around a little bit, temporary effect.
        self.player.punchAngle[2] = self.player.fallVelocity * 0.013
        if self.player.punchAngle[1] > 8:
            self.player.punchAngle[1] = 8

    def printData(self):
        print("move data at cmd num", self.player.currentCommand.commandNumber)
        print("buttons:", self.mv.buttons)
        print("old buttons:", self.mv.oldButtons)
        print("view angles:", self.mv.viewAngles)
        print("origin:", self.mv.origin)
        print("vel:", self.mv.velocity)
        print("wishmove:", self.mv.forwardMove, self.mv.sideMove, self.mv.upMove)
        print("on ground:", self.mv.onGround)
        print("max speed:", self.mv.maxSpeed)

    def fullWalkMove(self):
        #print("PRE WALK")
        #self.printData()

        #self.mv.onGround = self.isControllerOnGround()

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

        origVel = Vec3(self.mv.velocity)

        # Do the move.  This will clip our velocity and tell us if we are on
        # the ground.
        if self.mv.onGround:
            wasOnGround = True
            self.walkMove()
        else:
            wasOnGround = False
            self.airMove()

        #print("POST WALK")
        #self.printData()

        self.mv.onGround = bool(self.player.controller.collision_flags & PhysController.CFDown)
        if self.mv.onGround:
            #if not wasOnGround:
            #    # Landed.  Check
            self.player.airDashing = False

        self.checkVelocity()

        if not self.checkWater():
            self.finishGravity()

        if self.mv.onGround:
            self.mv.velocity[2] = 0.0

        self.checkFalling()

    def updateControllerSize(self):
        if self.player.ducked:
            self.player.controller.resize((VEC_DUCK_HULL_MAX.z - VEC_DUCK_HULL_MIN.z) * 0.5)
        else:
            self.player.controller.resize((VEC_HULL_MAX.z - VEC_HULL_MIN.z) * 0.5)

g_game_movement = GameMovement()

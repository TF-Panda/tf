""" DistributedTFPlayerShared module: contains the DistributedTFPlayerShared class

TF player code shared between AI (server) and client.

"""


from panda3d.core import *
from panda3d.pphysics import *

from .TFClass import *
from .InputButtons import *
from .ObserverMode import ObserverMode
from tf.tfbase import TFGlobals, TFFilters, Sounds, CollisionGroups

from tf.tfbase.SurfaceProperties import SurfaceProperties, SurfacePropertiesByPhysMaterial
from tf.weapon.TakeDamageInfo import TakeDamageInfo, calculateBulletDamageForce, addMultiDamage
from tf.movement.MoveType import MoveType
from tf.movement.GameMovement import g_game_movement
from tf.movement.MoveData import MoveData

from .TFPlayerState import TFPlayerState

import math
import random

tf_max_health_boost = 1.5

class DistributedTFPlayerShared:

    DiagonalFactor = math.sqrt(2.) / 2.

    StateNone = 0
    StateDead = 1
    StateAlive = 2

    CondNone = 0
    CondAiming = 1
    CondTaunting = 2
    CondSelectedToTeleport = 3
    CondDisguised = 4
    CondBurning = 5
    CondHealthBuff = 6
    CondInvulnerable = 7
    CondStealthedBlink = 8
    CondInvulnerableWearingOff = 9
    CondTeleported = 10
    CondZoomed = 11
    CondLoser = 12
    CondWinner = 13

    BadConditions = [
        CondBurning
    ]

    COND_COUNT = 13
    COND_PERMANENT = -1

    def __init__(self):
        self.playerName = ""
        self.tfClass = Class.Engineer
        self.classInfo = ClassInfos[self.tfClass]
        self.eyeH = 0.0
        self.eyeP = 0.0

        self.conditions = {}
        self.condition = self.CondNone

        self.viewModel = None

        #self.playerState = self.StateNone
        self.playerState = TFPlayerState.Fresh

        self.viewAngles = Vec3(0)

        self.animState = None

        self.lastPos = Point3(0)
        self.vel = Vec3()
        self.controller = None

        self.selectedBuilding = 0

        self.airDashing = False
        self.ducking = False

        self.stepSoundTime = 0.0
        self.stepSide = 0
        self.fallVelocity = 0.0

        self.observerMode = ObserverMode.Off
        self.observerTarget = -1

        self.buttons = InputFlag.Empty
        self.lastButtons = InputFlag.Empty
        self.buttonsPressed = InputFlag.Empty
        self.buttonsReleased = InputFlag.Empty

        self.weapons = []
        self.lastActiveWeapon = -1
        self.activeWeapon = -1

        # Variables used for GameMovement.
        self.moveType = MoveType.Walk
        self.duckTime = 0
        self.duckJumpTime = 0
        self.jumpTime = 0
        self.swimSoundTime = 0
        self.punchAngle = Vec3(0)
        self.punchAngleVel = Vec3(0)
        self.surfaceFriction = 1
        self.maxSpeed = 400
        self.onGround = False

        self.moveData = MoveData()

        self.tickBase = 0
        self.deathTime = 0.0

        self.objects = [-1, -1, -1, -1]

        self.metal = 0
        self.maxMetal = 200

        self.respawnTime = 0.0

        self.autoRezoom = False

        # Current FOV
        self.fov = 75
        # default fov
        self.defaultFov = 75
        self.desiredFov = 75
        self.fovSpeed = 0.0

        # List of players dominating me.
        self.nemesisList = []
        # List of players I am dominating.
        self.dominationList = []

        self.numDetonateables = 0

    def getLocalHullMins(self):
        return TFGlobals.VEC_HULL_MIN

    def getLocalHullMaxs(self):
        return TFGlobals.VEC_HULL_MAX

    def isLoser(self):
        return self.inCondition(self.CondLoser)

    def setFOV(self, fov, time):
        if fov == 0:
            self.fov = self.defaultFov
        else:
            self.fov = fov

    def __conditionThink(self, task):

        return task.cont

    def getMaxBuffedHealth(self):
        boostMax = self.maxHealth * tf_max_health_boost
        roundDown = int(boostMax / 5)
        roundDown *= 5
        return roundDown

    def getClassViewOffset(self):
        return Vec3(0, 0, self.classInfo.ViewOffset)

    def usesMetal(self):
        return self.tfClass == Class.Engineer

    def hasObject(self, objectType):
        return self.objects[objectType] != -1

    def setObject(self, objectType, doId):
        self.objects[objectType] = doId

    def removeObject(self, objectType):
        self.objects[objectType] = -1

    def updateClassSpeed(self):
        maxSpeed = 300 * self.classInfo.ForwardFactor

        if self.inCondition(self.CondLoser):
            maxSpeed *= 0.9
        elif self.inCondition(self.CondWinner):
            maxSpeed *= 1.1

        if self.inCondition(self.CondAiming):
            # Heavies and snipers aiming.
            if maxSpeed > 80:
                maxSpeed = 80

        self.maxSpeed = maxSpeed

    def setStepSoundTime(self, time, walking):
        if True:
            self.stepSoundTime = TFGlobals.remapValClamped(self.maxSpeed, 200, 450, 400, 200)
            if walking:
                self.stepSoundTime += 100

    def updateStepSound(self, origin, vel):
        dt = base.deltaTime
        if self.stepSoundTime > 0:
            self.stepSoundTime -= 1000.0 * dt
            if self.stepSoundTime < 0:
                self.stepSoundTime = 0

        if self.stepSoundTime > 0:
            return

        speed = vel.length()
        groundSpeed = vel.getXy().length()

        velRun = self.maxSpeed * 0.8
        velWalk = self.maxSpeed * 0.3

        onGround = self.onGround
        movingAlongGround = groundSpeed > 0.0001
        movingFastEnough = speed >= velWalk

        if not movingFastEnough or not (onGround and movingAlongGround):
            return

        walking = speed < velRun

        self.setStepSoundTime(0, walking)
        vol = 0.2 if walking else 0.5

        # TODO: if ducking vol *= 0.65

        self.playStepSound(origin, vol, False)

    def getPlayerCollideMask(self):
        """
        Returns the bitmask of collision groups that the player should
        collide with.
        """
        mask = CollisionGroups.World | CollisionGroups.PlayerClip
        # Collide with other team.
        if self.team == TFGlobals.TFTeam.Red:
            mask |= CollisionGroups.Mask_Blue
        else:
            mask |= CollisionGroups.Mask_Red
        return mask

    def playStepSound(self, origin, volume, force):
        if IS_CLIENT:
            # Only play footstep sound if first time predicted.
            if base.cr.prediction.inPrediction and not base.cr.prediction.firstTimePredicted:
                return

        origin = Point3(origin)

        # Trace down to get current ground material, ignoring player.
        surfaceDef = None
        tr = TFFilters.traceBox(origin, origin + Vec3.down() * 64,
            TFGlobals.VEC_HULL_MIN, TFGlobals.VEC_HULL_MAX,
            self.getPlayerCollideMask() & (~CollisionGroups.PlayerClip), TFFilters.TFQueryFilter(self))
        mat = tr['mat']
        if mat:
            # Get the surface definition associated with the PhysMaterial
            # the ray hit.
            surfaceDef = SurfacePropertiesByPhysMaterial.get(mat)
        if not surfaceDef:
            surfaceDef = SurfaceProperties['default']

        steps = [surfaceDef.stepLeft, surfaceDef.stepRight]
        stepSoundName = steps[self.stepSide]

        self.stepSide = not self.stepSide

        if IS_CLIENT:
            self.emitSound(stepSoundName, volume=volume)
        else:
            # On the server side, emit a spatial sound from the world so the
            # footstep sound doesn't follow the player.  Exclude the client
            # owner as they are predicting the sound and not spatializing it.
            base.world.emitSoundSpatial(stepSoundName, origin, volume=volume,
                                        excludeClients=[self.owner], chan=Sounds.Channel.CHAN_STATIC)

    def getPunchAngle(self):
        return self.punchAngle

    def setPunchAngle(self, ang):
        self.punchAngle = ang

    def getPunchAngleVel(self):
        return self.punchAngleVel

    def setPunchAngleVel(self, vel):
        self.punchAngleVel = vel

    def resetViewPunch(self, tolerance = 0):
        if tolerance != 0:
            tolerance *= tolerance
            check = self.punchAngleVel.lengthSquared() + self.punchAngle.lengthSquared()
            if check > tolerance:
                return
        self.punchAngle = Vec3(0)
        self.punchAngleVel = Vec3(0)

    def addViewPunch(self, ang):
        self.punchAngle += ang * 20

    def onAddCondition(self, cond):
        pass

    def onRemoveCondition(self, cond):
        pass

    def removeCondition(self, cond):
        hadIt = False
        if cond in self.conditions:
            hadIt = True
            del self.conditions[cond]
        self.condition &= ~(1 << cond)

        if hadIt:
            self.onRemoveCondition(cond)

    def removeAllConditions(self):
        for cond in self.conditions.keys():
            self.onRemoveCondition(cond)
        self.conditions = {}
        self.condition = 0

    def setCondition(self, cond, time=-1):
        hadIt = cond in self.conditions
        self.conditions[cond] = time
        self.condition |= (1 << cond)
        if not hadIt:
            self.onAddCondition(cond)

    def inCondition(self, cond):
        return self.condition & (1 << cond)

    def isObserver(self):
        return self.observerMode != ObserverMode.Off

    def doClassSpecialSkill(self):
        pass

    def doAnimationEvent(self, event, data = 0, predicted=True):
        pass

    def fireBullet(self, info, doEffects, damageType, customDamageType):
        # Fire a bullet (ignoring the shooter).
        start = info['src']
        end = start + info['dirShooting'] * info['distance']
        tr = TFFilters.traceLine(start, end, CollisionGroups.Mask_BulletCollide, TFFilters.TFQueryFilter(self))

        impactVol = 1.0 / info['shots']

        if tr['hit']:
            # Bullet hit something!

            tracerAttachment = info.get('tracerAttachment', None)
            if tracerAttachment:
                tracerDelay = info.get('tracerDelay', 0.0)
                tracerSpread = info.get('tracerSpread', 0.0)
                if not IS_CLIENT:
                    info['weapon'].sendUpdate('fireTracer', [tracerAttachment, tr['endpos'], tracerDelay, tracerSpread], excludeClients=[self.owner])
                elif base.cr.prediction.firstTimePredicted:
                    self.viewModel.tracerRequests.append((tr['endpos'], tracerDelay, tracerSpread))

            entity = tr['ent']
            if not entity:
                # Didn't hit an entity.  Hmm.
                return

            # Play bullet impact sound for material we hit.
            if not IS_CLIENT:
                # Don't send to client who predicted it.
                if self.owner is not None:
                    exclude = [self.owner]
                else:
                    exclude = []
                physMat = tr['mat']
                surfaceDef = SurfacePropertiesByPhysMaterial.get(physMat)
                if not surfaceDef:
                    surfaceDef = SurfaceProperties['default']
                base.world.emitSoundSpatial(surfaceDef.bulletImpact, tr['endpos'], excludeClients=exclude, volume=impactVol, chan=Sounds.Channel.CHAN_STATIC)
                entity.traceDecal(surfaceDef.impactDecal, tr, excludeClients=exclude)
            else:
                if base.cr.prediction.firstTimePredicted:
                    physMat = tr['mat']
                    surfaceDef = SurfacePropertiesByPhysMaterial.get(physMat)
                    if not surfaceDef:
                        surfaceDef = SurfaceProperties['default']
                    base.world.emitSoundSpatial(surfaceDef.bulletImpact, tr['endpos'], volume=impactVol, chan=Sounds.Channel.CHAN_STATIC)
                    entity.traceDecal(surfaceDef.impactDecal, tr)

            if doEffects:
                # TODO
                pass

            if not IS_CLIENT:
                # Server-specific.
                dmgInfo = TakeDamageInfo()
                dmgInfo.inflictor = self
                dmgInfo.attacker = self
                dmgInfo.setDamage(info['damage'])
                dmgInfo.damageType = damageType
                dmgInfo.customDamage = customDamageType
                calculateBulletDamageForce(dmgInfo, Vec3(info['dirShooting']), tr['endpos'], 1.0)
                entity.dispatchTraceAttack(dmgInfo, info['dirShooting'], tr)

    def updateButtonsState(self, buttons):
        self.lastButtons = self.buttons
        self.buttons = buttons

        buttonsChanged = self.lastButtons ^ self.buttons

        # Debounced button codes for pressed/release
        self.buttonsPressed = buttonsChanged & self.buttons
        self.buttonsReleased = buttonsChanged & (~self.buttons)

    def getWeapons(self):
        return self.weapons

    def getLastActiveWeapon(self):
        return self.lastActiveWeapon

    def getActiveWeapon(self):
        return self.activeWeapon

    def hasActiveWeapon(self):
        return self.activeWeapon >= 0 and self.activeWeapon < len(self.weapons)

    def getActiveWeaponObj(self):
        """
        Returns the DistributedObject of the player's currently active weapon,
        or None if he has no active weapon, or the DO doesn't exist.
        """
        if not self.hasActiveWeapon():
            return None
        return base.net.doId2do.get(self.weapons[self.activeWeapon])

    def setupController(self):
        self.disableController()

        mins = TFGlobals.VEC_HULL_MIN
        maxs = TFGlobals.VEC_HULL_MAX
        halfExts = Vec3((maxs[0] - mins[0]) / 2, (maxs[1] - mins[1]) / 2, (maxs[2] - mins[2]) / 2)
        mat = SurfaceProperties[self.getModelSurfaceProp()].getPhysMaterial()
        self.controller = PhysBoxController(
            base.physicsWorld, self,
            halfExts, mat
        )
        self.applyControllerMasks()

        self.controller.setUpDirection(Vec3.up())
        self.controller.setStepOffset(24) # 18 HUs to inches?
        self.controller.setContactOffset(1) # 6 inches idk
        self.controller.setFootPosition(self.getPos())
        self.controller.getActorNode().setPythonTag("entity", self)
        self.controller.getActorNode().setPythonTag("object", self)

    def applyControllerMasks(self):
        if self.team == TFGlobals.TFTeam.Red:
            # We are red team.
            self.controller.setFromCollideMask(CollisionGroups.RedPlayer)
        else:
            self.controller.setFromCollideMask(CollisionGroups.BluePlayer)
        #self.controller.setIntoCollideMask(self.getPlayerCollideMask())

    def disableController(self):
        """
        Disables the controller.  Will not collide with anything until
        enableController() is called.
        """

        if self.controller:
            self.controller.destroy()
            self.controller = None

    def enableController(self):
        """
        Re-enables the controller.  Collisions will occur with the controller
        again.
        """
        if not self.controller:
            self.setupController()

    def announceGenerate(self):
        self.classInfo = ClassInfos[self.tfClass]
        #self.setupController()

    def runPlayerCommand(self, command, deltaTime):
        if not self.controller:
            return

        self.controller.foot_position = self.getPos()

        dt = deltaTime

        forward = command.buttons & InputFlag.MoveForward
        reverse = command.buttons & InputFlag.MoveBackward
        left = command.buttons & InputFlag.MoveLeft
        right = command.buttons & InputFlag.MoveRight

        self.moveData.player = self
        self.moveData.origin = Point3(self.getPos())
        self.moveData.oldAngles = Vec3(self.moveData.angles)
        self.moveData.angles = Vec3(command.viewAngles)
        self.moveData.viewAngles = Vec3(command.viewAngles)
        self.moveData.oldButtons = self.lastButtons
        self.moveData.buttons = command.buttons
        self.moveData.clientMaxSpeed = self.maxSpeed
        self.moveData.velocity = Vec3(self.velocity)
        self.moveData.onGround = self.onGround
        self.moveData.firstRunOfFunctions = True

        self.moveData.forwardMove = command.move[1]
        self.moveData.sideMove = command.move[0]
        self.moveData.upMove = command.move[2]

        # Run the movement.
        g_game_movement.processMovement(self, self.moveData)

        # Extract the new position.
        self.velocity = Vec3(self.moveData.velocity)
        self.lastButtons = self.moveData.buttons
        self.onGround = self.moveData.onGround
        self.maxSpeed = self.moveData.maxSpeed
        self.setPos(self.moveData.origin)
        self.lastPos = self.getPos()
        self.vel = -self.moveData.velocity

    def disable(self):
        self.controller = None
        self.viewModel = None
        if self.animState:
            self.animState.delete()
            self.animState = None

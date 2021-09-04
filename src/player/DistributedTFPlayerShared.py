""" DistributedTFPlayerShared module: contains the DistributedTFPlayerShared class

TF player code shared between AI (server) and client.

"""


from panda3d.core import *
from panda3d.pphysics import *

from .TFClass import *
from .InputButtons import *
from .ObserverMode import ObserverMode
from tf.tfbase import TFGlobals, TFFilters

from tf.tfbase.TFGlobals import Contents, CollisionGroup
from tf.weapon.TakeDamageInfo import TakeDamageInfo, calculateBulletDamageForce, addMultiDamage
from tf.movement.MoveType import MoveType
from tf.movement.GameMovement import g_game_movement
from tf.movement.MoveData import MoveData

import math

class DistributedTFPlayerShared:

    DiagonalFactor = math.sqrt(2.) / 2.

    StateNone = 0
    StateDead = 1
    StateAlive = 2

    def __init__(self):
        self.playerName = ""
        self.tfClass = Class.Engineer
        self.classInfo = ClassInfos[self.tfClass]
        self.eyeH = 0.0
        self.eyeP = 0.0

        self.viewModel = None

        self.playerState = self.StateNone

        self.viewAngles = Vec3(0)

        self.animState = None

        self.lastPos = Point3(0)
        self.vel = Vec3()
        self.controller = None

        self.observerMode = ObserverMode.Off
        self.observerTarget = -1

        self.buttons = InputFlag.Empty
        self.lastButtons = InputFlag.Empty
        self.buttonsPressed = InputFlag.Empty
        self.buttonsReleased = InputFlag.Empty

        self.weapons = []
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
        self.maxSpeed = 320
        self.onGround = False

        self.moveData = MoveData()

        self.tickBase = 0
        self.deathTime = 0.0

    def isObserver(self):
        return self.observerMode != ObserverMode.Off

    def doClassSpecialSkill(self):
        pass

    def doAnimationEvent(self, event, data = 0):
        pass

    def fireBullet(self, info, doEffects, damageType, customDamageType):
        # Fire a bullet (ignoring the shooter).
        start = info['src']
        #end = start + info['dirShooting'] * info['distance']
        result = PhysRayCastResult()
        filter = TFFilters.TFQueryFilter(self)
        base.physicsWorld.raycast(result, start, info['dirShooting'], info['distance'],
                                  BitMask32(Contents.HitBox | Contents.AnyTeam | Contents.Solid), BitMask32.allOff(),
                                  CollisionGroup.Empty, filter)
        if result.hasBlock():
            # Bullet hit something!
            block = result.getBlock()
            actor = block.getActor()
            entity = actor.getPythonTag("entity")
            if not entity:
                # Didn't hit an entity.  Hmm.
                return

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
                calculateBulletDamageForce(dmgInfo, Vec3(info['dirShooting']), block.getPosition(), 1.0)
                entity.dispatchTraceAttack(dmgInfo, info['dirShooting'], block)

    def updateButtonsState(self, buttons):
        self.lastButtons = self.buttons
        self.buttons = buttons

        buttonsChanged = self.lastButtons ^ self.buttons

        # Debounced button codes for pressed/release
        self.buttonsPressed = buttonsChanged & self.buttons
        self.buttonsReleased = buttonsChanged & (~self.buttons)

    def getWeapons(self):
        return self.weapons

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
        mins = TFGlobals.VEC_HULL_MIN
        maxs = TFGlobals.VEC_HULL_MAX
        halfExts = Vec3((maxs[0] - mins[0]) / 2, (maxs[1] - mins[1]) / 2, (maxs[2] - mins[2]) / 2)
        mat = PhysMaterial(0.3, 0.3, 0.0)
        self.controller = PhysBoxController(
            base.physicsWorld, self,
            halfExts, mat
        )
        self.controller.setCollisionGroup(TFGlobals.CollisionGroup.PlayerMovement)
        if self.team == 0:
            # We are red team.
            self.controller.setContentsMask(TFGlobals.Contents.RedTeam)
            # Blue team is solid to us.
            self.controller.setSolidMask(TFGlobals.Contents.BlueTeam | TFGlobals.Contents.Solid)
        elif self.team == 1:
            # We are blue team.
            self.controller.setContentsMask(TFGlobals.Contents.BlueTeam)
            # Red team is solid to us.
            self.controller.setSolidMask(TFGlobals.Contents.RedTeam | TFGlobals.Contents.Solid)

        self.controller.setUpDirection(Vec3.up())
        self.controller.setFootPosition(self.getPos())
        #self.controller.setContactOffset(0.00001)
        self.controller.getActorNode().setPythonTag("entity", self)
        self.attachNewNode(self.controller.getActorNode())

    def disableController(self):
        if self.controller:
            self.controller.getActorNode().removeFromScene(base.physicsWorld)

    def enableController(self):
        if self.controller:
            self.controller.getActorNode().addToScene(base.physicsWorld)

    def announceGenerate(self):
        self.classInfo = ClassInfos[self.tfClass]
        self.setupController()

    def runPlayerCommand(self, command, deltaTime):

        self.controller.setFootPosition(self.getPos())

        dt = deltaTime

        forward = command.buttons & InputFlag.MoveForward
        reverse = command.buttons & InputFlag.MoveBackward
        left = command.buttons & InputFlag.MoveLeft
        right = command.buttons & InputFlag.MoveRight

        self.moveData.player = self
        self.moveData.origin = self.getPos()
        self.moveData.oldAngles = Vec3(self.moveData.angles)
        self.moveData.angles = command.viewAngles
        self.moveData.viewAngles = command.viewAngles
        self.moveData.oldButtons = self.lastButtons
        self.moveData.buttons = self.buttons
        self.moveData.clientMaxSpeed = self.maxSpeed
        self.moveData.velocity = Vec3(self.velocity)
        self.moveData.onGround = self.onGround

        self.moveData.forwardMove = command.move[1]
        self.moveData.sideMove = command.move[0]
        self.moveData.upMove = command.move[2]

        # Run the movement.
        g_game_movement.processMovement(self, self.moveData)

        # Extract the new position.
        self.velocity = Vec3(self.moveData.velocity)
        self.oldButtons = self.moveData.buttons
        self.onGround = self.moveData.onGround
        self.maxSpeed = self.moveData.maxSpeed
        self.setPos(self.moveData.origin)
        self.lastPos = self.getPos()
        self.vel = -self.moveData.velocity

    def disable(self):
        self.controller = None
        self.viewModel = None

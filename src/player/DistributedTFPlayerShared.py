""" DistributedTFPlayerShared module: contains the DistributedTFPlayerShared class

TF player code shared between AI (server) and client.

"""


from panda3d.core import *

from panda3d.pphysics import PhysBoxController, PhysMaterial

from .TFClass import *
from .InputButtons import *
from tf.tfbase import TFGlobals

from tf.movement.MoveType import MoveType
from tf.movement.GameMovement import g_game_movement
from tf.movement.MoveData import MoveData

import math

class DistributedTFPlayerShared:

    DiagonalFactor = math.sqrt(2.) / 2.

    def __init__(self):
        self.playerName = ""
        self.tfClass = 0
        self.lookPitch = 0.0
        self.lookYaw = 0.0
        self.moveX = 0.0
        self.moveY = 0.0

        self.viewAngles = Vec3(0)

        self.animState = None

        self.lastPos = Point3(0)
        self.vel = Vec3()
        self.controller = None

        self.buttons = InputFlag.Empty

        self.weapons = []
        self.activeWeapon = -1

        # Variables used for GameMovement.
        self.moveType = MoveType.Walk
        self.duckTime = 0
        self.duckJumpTime = 0
        self.jumpTime = 0
        self.swimSoundTime = 0
        self.punchAngle = Vec3(0)
        self.waterLevel = 0
        self.gravity = 1.0
        self.baseVelocity = Vec3(0)
        self.surfaceFriction = 1

        self.moveData = MoveData()

    def getWeapons(self):
        return self.weapons

    def getActiveWeapon(self):
        return self.activeWeapon

    def setupController(self):
        mins = self.classInfo.BBox[0]
        maxs = self.classInfo.BBox[1]
        halfExts = Vec3((maxs[0] - mins[0]) / 2, (maxs[1] - mins[1]) / 2, (maxs[2] - mins[2]) / 2)
        mat = PhysMaterial(0.3, 0.3, 0.0)
        self.controller = PhysBoxController(
            base.physicsWorld, self,
            halfExts, mat
        )
        self.controller.setCollisionGroup(TFGlobals.CollisionGroup.Empty)
        # We are red team.
        self.controller.setContentsMask(TFGlobals.Contents.RedTeam)
        # Blue team is solid to us.
        self.controller.setSolidMask(TFGlobals.Contents.RedTeam)
        self.controller.setUpDirection(Vec3.up())
        self.controller.setFootPosition(self.getPos())

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

        self.moveData.origin = self.getPos()
        self.moveData.angles = self.getHpr()
        self.moveData.viewAngles = command.viewAngles
        self.moveData.oldButtons = self.moveData.buttons
        self.moveData.buttons = command.buttons
        self.moveData.clientMaxSpeed = 320

        self.moveData.forwardMove = 0
        self.moveData.sideMove = 0

        if forward:
            self.moveData.forwardMove += BaseSpeed * self.classInfo.ForwardFactor
        if reverse:
            self.moveData.forwardMove -= BaseSpeed * self.classInfo.BackwardFactor
        if right:
            self.moveData.sideMove += BaseSpeed * self.classInfo.ForwardFactor
        if left:
            self.moveData.sideMove -= BaseSpeed * self.classInfo.ForwardFactor

        # Run the movement.
        g_game_movement.processMovement(self, self.moveData)

        # Extract the new position.
        self.setPos(self.moveData.origin)
        self.lastPos = self.getPos()
        self.vel = -self.moveData.velocity

    def disable(self):
        self.controller = None

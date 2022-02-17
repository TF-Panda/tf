from panda3d.core import *

from tf.player.InputButtons import InputFlag
from tf.movement.MoveType import MoveType

class MoveData:

    def __init__(self):
        # True if this is the first time the movement is being
        # predicted.
        self.firstRunOfFunctions = False

        # Handle to the DistributedTFPlayer we are moving.
        self.player = None

        # Button state for this move.
        self.buttons = InputFlag.Empty

        # Button state from last move.
        self.oldButtons = InputFlag.Empty

        # Velocities the player wishes to move in on each axis,
        # relative to view angles.
        self.wishMove = Vec3(0)

        # Euler angles of the player's current view.
        # Wish move velocity is rotated by the view angles.
        self.viewAngles = Vec3(0)

        # Current player position.
        self.origin = Point3(0)

        # The maximum velocity the player is allowed to have under any
        # circumstances.
        self.maxSpeed = 0.0

        self.moveType = MoveType.Walk

        self.viewAngles = Vec3(0)
        self.origin = Point3(0)
        self.angles = Vec3(0)
        self.oldAngles = Vec3(0)
        self.forwardMove = 0.0
        self.sideMove = 0.0
        self.upMove = 0.0
        self.maxSpeed = 0.0
        self.clientMaxSpeed = 0.0
        self.velocity = Vec3(0)
        self.outWishVel = Vec3(0)
        self.outJumpVel = Vec3(0)
        self.outStepHeight = 0.0
        self.onGround = True

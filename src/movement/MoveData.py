from panda3d.core import *

from tf.player.InputButtons import InputFlag

class MoveData:

    def __init__(self):
        self.buttons = InputFlag.Empty
        self.oldButtons = InputFlag.Empty
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

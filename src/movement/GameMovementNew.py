"""GameMovement module: contains the GameMovement class."""

from panda3d.core import *
from panda3d.pphysics import *

class GameMovement:

    def runMovement(self, moveData):
        assert moveData.player
        # Store off the input parameters.
        self.mv = moveData

        # Compute some stuff once.
        self.buttonsChanged = self.mv.buttons ^ self.mv.oldButtons
        self.buttonsPressed = self.buttonsChanged & self.mv.buttons
        self.buttonsReleased = self.buttonsChanged & self.mv.oldButtons

        self.playerMove()
        self.finishMove()

    def canAccelerate(self):
        """
        Returns true if the player is allowed to accelerate.
        Might be false under certain conditions.
        """
        return True

    def checkParameters(self):
        """
        Makes sure the input move data velocities are
        in-check.
        """

        if self.mv.moveType != MoveType.Isometric and \
            self.mv.moveType != MoveType.NoClip and \
            self.mv.moveType != MoveType.Observer:

            # If we want to move faster than the max speed, scale it
            # down.
            speed = self.mv.wishMove.lengthSquared()
            if speed != 0.0 and speed > self.mv.maxSpeed*self.mv.maxSpeed:
                # Scale wish move down to max speed.
                ratio = self.mv.maxSpeed / math.sqrt(speed)
                self.mv.wishMove *= ratio

        if self.player.isDead():
            self.mv.wishMove.set(0, 0, 0)

        self.decayPunchAngle()


        q = Quat()
        q.setHpr(self.mv.viewAngles)
        # Rotate wish move by view angles to get world-space wish move.
        self.wishMoveWorld = q.xform(self.wishMove)
        self.viewForward = q.getForward()
        self.viewRight = q.getRight()
        self.viewUp = q.getUp()
        self.viewQuat = q

    def playerMove(self):


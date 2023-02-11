"""DistributedFuncDoor module: contains the DistributedFuncDoor class."""

from .DistributedSolidEntity import DistributedSolidEntity

from panda3d.core import *

from tf.tfbase.TFGlobals import SolidShape, SolidFlag
from tf.tfbase import Sounds

class DistributedFuncDoor(DistributedSolidEntity):

    """
    A brush-based sliding door.
    """

    DSClosed = 0
    DSClosing = 1
    DSOpening = 2
    DSOpen = 3

    NeedOrigin = True

    FlagsToggle = 32

    def __init__(self):
        DistributedSolidEntity.__init__(self)

        self.physType = self.PTTriangles
        self.solidShape = SolidShape.Model
        self.solidFlags = SolidFlag.Tangible

        self.doorState = self.DSClosed

        self.enabled = True

        # Direction door should move to open.
        self.moveQuat = Quat.identQuat()
        self.moveDir = Vec3.up()
        # How long to wait after opening to automatically close.
        # -1 stays open forever or until an explicit call to close().
        self.wait = -1.0
        # Units per sec opening/closing speed.
        self.speed = 1.0
        # Number of units to offset open position along opposite of moveDir.
        self.lip = 0.0

        self.openPos = Point3()
        self.moveLen = 1.0
        self.fracsPerSec = 1.0

        self.closeTime = -1.0

        # Door open fraction.  0.0 is fully closed, 1.0 is fully open.
        self.frac = 0.0

    if not IS_CLIENT:

        def initFromLevel(self, ent, props):
            DistributedSolidEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("movedir"):
                # Direction door should slide.
                phr = Vec3()
                phrStr = props.getAttributeValue("movedir").getString().split()
                phr[0] = float(phrStr[0])
                phr[1] = float(phrStr[1])
                phr[2] = float(phrStr[2])
                q = Quat()
                q.setHpr((phr[1] - 90, -phr[0], phr[2]))
                self.moveQuat = q
                self.moveDir = q.getForward()
            if props.hasAttribute("lip"):
                self.lip = props.getAttributeValue("lip").getFloat()
            if props.hasAttribute("speed"):
                self.speed = props.getAttributeValue("speed").getFloat()
            if props.hasAttribute("wait"):
                self.wait = props.getAttributeValue("wait").getFloat()
            if props.hasAttribute("spawnflags"):
                sf = props.getAttributeValue("spawnflags").getInt()
                if sf & self.FlagsToggle:
                    self.wait = -1

        def input_Open(self, caller):
            self.openDoor()

        def input_Close(self, caller):
            self.closeDoor()

        def openDoor(self):
            if self.doorState <= self.DSClosing:
                self.doorState = self.DSOpening
                self.emitSoundSpatial("DoorSound.DefaultMove")
                self.connMgr.fireOutput("OnOpen")

        def closeDoor(self):
            if self.doorState >= self.DSOpening:
                self.doorState = self.DSClosing
                #self.emitSoundSpatial("DoorSound.DefaultMove")
                self.connMgr.fireOutput("OnClose")

        def __doorUpdate(self, task):

            if self.doorState == self.DSClosing:
                self.frac -= self.fracsPerSec * globalClock.dt
                self.frac = max(0.0, self.frac)
                if self.frac <= 0:
                    self.doorState = self.DSClosed
                    self.emitSoundSpatial("DoorSound.DefaultArrive")

                self.setPos(self.closedPos + self.openPos * self.frac)

            elif self.doorState == self.DSOpening:
                self.frac += self.fracsPerSec * globalClock.dt
                self.frac = min(1.0, self.frac)
                if self.frac >= 1:
                    self.doorState = self.DSOpen
                    self.stopSound(Sounds.Channel.CHAN_BODY)
                    #self.emitSoundSpatial("DoorSound.DefaultArrive")
                    if self.wait >= 0.0:
                        self.closeTime = globalClock.frame_time + self.wait

                self.setPos(self.closedPos + self.openPos * self.frac)

            elif self.doorState == self.DSOpen:
                if self.closeTime >= 0 and globalClock.frame_time >= self.closeTime:
                    self.closeDoor()

            return task.cont

    def announceGenerate(self):
        DistributedSolidEntity.announceGenerate(self)
        if not IS_CLIENT:
            # The move offset is the extents of the model bounding box.
            extents = self.model.getMaxs() - self.model.getMins()
            # Shrink by lip.
            extents -= self.lip
            # Modulate by move direction vector.
            extents.componentwiseMult(self.moveDir)
            # Initial position is closed position.
            self.closedPos = self.getPos()
            # This is an offset to the closed position to make it open.
            self.openPos = extents
            self.moveLen = self.openPos.length()
            self.fracsPerSec = self.speed / self.moveLen

            self.addTask(self.__doorUpdate, 'doorUpdate', appendTask=True)

        self.initializeCollisions()

if not IS_CLIENT:
    DistributedFuncDoorAI = DistributedFuncDoor
    DistributedFuncDoorAI.__name__ = 'DistributedFuncDoorAI'

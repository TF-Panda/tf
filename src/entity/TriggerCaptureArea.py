"""TriggerCaptureArea module: contains the TriggerCaptureArea class."""

from . import CapState
from .DistributedTrigger import DistributedTrigger


class TriggerCaptureArea(DistributedTrigger):
    """
    Client-side capture area.
    """

    def __init__(self):
        DistributedTrigger.__init__(self)

        self.capDoId = 0
        self.capPoint = None
        self.capState = CapState.CSIdle
        self.capSound = None

    def announceGenerate(self):
        DistributedTrigger.announceGenerate(self)
        self.getCapPoint()

    def getCapPoint(self):
        self.capPoint = base.cr.doId2do.get(self.capDoId)

    def RecvProxy_capDoId(self, doId):
        if not self.capPoint or doId != self.capDoId:
            self.capDoId = doId
            self.getCapPoint()

    def disable(self):
        if self.capSound:
            self.capSound.stop()
            self.capSound = None
        self.capPoint = None
        DistributedTrigger.disable(self)

    def doCapSound(self, soundName):
        if self.capSound:
            self.capSound.stop()
            self.capSound = None
        if self.capPoint:
            self.capSound = self.capPoint.emitSoundSpatial(soundName)

    def RecvProxy_capState(self, state):
        self.setCapState(state)

    def setCapState(self, state):
        if state != self.capState:
            if state in (CapState.CSCapping, CapState.CSReverting):
                self.doCapSound("Hologram.Start")
            elif state == CapState.CSBlocked:
                self.doCapSound("Hologram.Interrupted")
            elif state == CapState.CSIdle:
                self.doCapSound("Hologram.Stop")
            self.capState = state

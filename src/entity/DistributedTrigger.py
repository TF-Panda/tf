"""DistributedTrigger module: contains the DistributedTrigger class."""

from .DistributedSolidEntity import DistributedSolidEntity

from tf.tfbase.TFGlobals import SolidShape, SolidFlag, Contents, WorldParent

class DistributedTrigger(DistributedSolidEntity):

    def __init__(self):
        DistributedSolidEntity.__init__(self)
        self.physType = self.PTConvex
        self.solidShape = SolidShape.Model
        self.solidFlags = SolidFlag.Trigger
        self.solidMask = Contents.Solid | Contents.RedTeam | Contents.BlueTeam
        self.triggerCallback = True
        self.parentEntityId = WorldParent.Hidden

    if not IS_CLIENT:
        def announceGenerate(self):
            DistributedSolidEntity.announceGenerate(self)
            self.initializeCollisions()

        def onTriggerEnter(self, entity):
            if entity.isPlayer() and not entity.isDead():
                self.connMgr.fireOutput("OnStartTouchAll", activator=entity)

        def onTriggerExit(self, entity):
            if entity.isPlayer() and not entity.isDead():
                self.connMgr.fireOutput("OnEndTouchAll", activator=entity)

if not IS_CLIENT:
    DistributedTriggerAI = DistributedTrigger
    DistributedTriggerAI.__name__ = 'DistributedTriggerAI'

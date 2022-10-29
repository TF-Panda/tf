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
        self.triggerEnabled = True

    if not IS_CLIENT:
        def announceGenerate(self):
            DistributedSolidEntity.announceGenerate(self)
            self.initializeCollisions()

        def initFromLevel(self, ent, props):
            DistributedSolidEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("StartDisabled"):
                self.triggerEnabled = not props.getAttributeValue("StartDisabled").getBool()

        def onTriggerEnter(self, entity):
            if not self.triggerEnabled:
                return
            if entity.isPlayer() and not entity.isDead():
                self.connMgr.fireOutput("OnStartTouchAll", activator=entity)

        def onTriggerExit(self, entity):
            if not self.triggerEnabled:
                return
            if entity.isPlayer() and not entity.isDead():
                self.connMgr.fireOutput("OnEndTouchAll", activator=entity)

        def input_Enable(self, caller):
            self.triggerEnabled = True

if not IS_CLIENT:
    DistributedTriggerAI = DistributedTrigger
    DistributedTriggerAI.__name__ = 'DistributedTriggerAI'

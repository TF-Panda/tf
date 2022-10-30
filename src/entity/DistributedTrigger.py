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
        self.filterName = ""
        self.filterEnt = None

    if not IS_CLIENT:
        def announceGenerate(self):
            DistributedSolidEntity.announceGenerate(self)
            self.initializeCollisions()

            if self.filterName:
                ents = base.entMgr.findEntity(self.filterName)
                if ents:
                    self.filterEnt = ents[0]

        def initFromLevel(self, ent, props):
            DistributedSolidEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("StartDisabled"):
                self.triggerEnabled = not props.getAttributeValue("StartDisabled").getBool()
            if props.hasAttribute("filtername"):
                self.filterName = props.getAttributeValue("filtername").getString()

        def onEntityStartTouch(self, entity):
            self.connMgr.fireOutput("OnStartTouchAll", activator=entity)

        def onEntityEndTouch(self, entity):
            self.connMgr.fireOutput("OnEndTouchAll", activator=entity)

        def onTriggerEnter(self, entity):
            if not self.triggerEnabled:
                return
            if not entity.isPlayer():
                return
            if entity.isDead():
                return
            if self.filterEnt:
                if not self.filterEnt.testFilter(entity):
                    return

            self.onEntityStartTouch(entity)

        def onTriggerExit(self, entity):
            if not self.triggerEnabled:
                return
            if not entity.isPlayer():
                return
            if entity.isDead():
                return
            if self.filterEnt:
                if not self.filterEnt.testFilter(entity):
                    return

            self.onEntityEndTouch(entity)

        def input_Enable(self, caller):
            self.triggerEnabled = True

if not IS_CLIENT:
    DistributedTriggerAI = DistributedTrigger
    DistributedTriggerAI.__name__ = 'DistributedTriggerAI'

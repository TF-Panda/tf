
from tf.entity.DistributedEntity import DistributedEntityAI
from .Actor import Actor

from tf.tfbase.TFGlobals import SolidShape

from .AnimEvents import AnimEventType

class DistributedCharAI(Actor, DistributedEntityAI):

    def __init__(self):
        Actor.__init__(self)
        DistributedEntityAI.__init__(self)

        self.lastEventCheck = 0.0

    def delete(self):
        self.cleanup()
        DistributedEntityAI.delete(self)

    def onModelChanged(self):
        self.initializeCollisions()
        if self.modelNp:
            # Parent model to entity.
            self.modelNp.reparentTo(self)
        Actor.onModelChanged(self)

    def loadModelBBoxIntoHull(self):
        data = self.modelData
        if not data:
            return
        if not data.hasAttribute("bbox"):
            return
        bbox = data.getAttributeValue("bbox").getElement()
        if not bbox:
            return
        assert bbox.hasAttribute("mins") and bbox.hasAttribute("maxs")
        bbox.getAttributeValue("mins").toVec3(self.hullMins)
        bbox.getAttributeValue("maxs").toVec3(self.hullMaxs)

    def initializeCollisions(self):
        if self.solidShape == SolidShape.Model:
            assert self.modelRootNode
            cinfo = self.modelRootNode.getCollisionInfo()
            if cinfo:
                cinfo = cinfo.getPart(0)
                assert cinfo
                self.mass = cinfo.mass
                self.damping = cinfo.damping
                self.rotDamping = cinfo.rot_damping

        elif self.solidShape == SolidShape.Box:
            self.loadModelBBoxIntoHull()

        DistributedEntityAI.initializeCollisions(self)

    def makeModelCollisionShape(self):
        return Actor.makeModelCollisionShape(self)

    def dispatchAnimEvents(self, handler):
        if not self.character:
            return

        queue = AnimEventQueue()
        self.character.getEvents(queue, AnimEventType.Server)

        while queue.hasEvent():
            info = queue.popEvent()
            channel = self.character.getChannel(info.channel)
            event = channel.getEvent(info.event)
            eventInfo = {
                "eventTime": globalClock.frame_time,
                "source": self,
                "sequence": info.channel,
                "cycle": event.getCycle(),
                "event": event.getEvent(),
                "options": event.getOptions(),
                "type": event.getType()}
            handler.handleAnimEvent(eventInfo)

    def setModel(self, filename):
        self.loadModel(filename)

    def SendProxy_skin(self):
        return self.skin

    def loadModel(self, model):
        Actor.loadModel(self, model)
        # The server doesn't blend sequence transitions or interpolate
        # animation frames.
        self.setChannelTransition(False)
        self.setFrameBlend(False)

    def simulate(self):
        DistributedEntityAI.simulate(self)

        if self.character:
            # Compute the animation.   This also advances the anim time and
            # cycle on the sequence player, which will be sent to clients.
            self.character.update()

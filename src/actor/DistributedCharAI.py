
from tf.entity.DistributedEntity import DistributedEntityAI
from .Char import Char

from tf.tfbase.TFGlobals import SolidShape

from .AnimEvents import AnimEventType

class DistributedCharAI(Char, DistributedEntityAI):

    def __init__(self):
        Char.__init__(self)
        DistributedEntityAI.__init__(self)

        self.lastEventCheck = 0.0

    def delete(self):
        Char.delete(self, removeNode=False)
        DistributedEntityAI.delete(self)

    def onModelChanged(self):
        self.initializeCollisions()
        Char.onModelChanged(self)

    def loadModelBBoxIntoHull(self):
        if not self.modelNp:
            return
        data = self.modelNp.node().getCustomData()
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
            assert self.modelNp
            cinfo = self.modelNp.node().getCollisionInfo().getPart(0)
            assert cinfo
            self.mass = cinfo.mass
            self.damping = cinfo.damping
            self.rotDamping = cinfo.rot_damping

        elif self.solidShape == SolidShape.Box:
            self.loadModelBBoxIntoHull()

        DistributedEntityAI.initializeCollisions(self)

    def makeModelCollisionShape(self):
        return Char.makeModelCollisionShape(self)

    def dispatchAnimEvents(self, handler):
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
        Char.loadModel(self, model)
        # The server doesn't blend sequence transitions.
        self.setBlend(transitionBlend=False)

    def simulate(self):
        DistributedEntityAI.simulate(self)

        if self.character:
            # Compute the animation.   This also advances the anim time and
            # cycle on the sequence player, which will be sent to clients.
            self.character.update()

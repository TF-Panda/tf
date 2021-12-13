
from tf.entity.DistributedEntity import DistributedEntityAI
from .Char import Char

from tf.tfbase.TFGlobals import SolidShape

from .AnimEvents import AnimEventType

class DistributedCharAI(Char, DistributedEntityAI):

    def __init__(self):
        Char.__init__(self)
        DistributedEntityAI.__init__(self)
        self.animTime = 0.0

        self.clientSideAnimation = False

        self.lastEventCheck = 0.0

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

    def SendProxy_skin(self):
        return self.getSkin()

    def SendProxy_newSequenceParity(self):
        return self.getNewSequenceParity()

    def SendProxy_playMode(self):
        return self.character.getAnimLayer(0)._play_mode

    def SendProxy_startCycle(self):
        return self.character.getAnimLayer(0)._start_cycle

    def SendProxy_playCycles(self):
        return self.character.getAnimLayer(0)._play_cycles

    def SendProxy_sequence(self):
        curr = self.getCurrSequence()
        return curr

    def SendProxy_cycle(self):
        cycle =  self.getCycle()
        return cycle

    def SendProxy_playRate(self):
        pr =  self.getPlayRate()
        return pr

    def dispatchAnimEvents(self, handler):
        queue = AnimEventQueue()
        self.character.getEvents(queue, AnimEventType.Server)

        while queue.hasEvent():
            info = queue.popEvent()
            channel = self.character.getChannel(info.channel)
            event = channel.getEvent(info.event)
            eventInfo = {
                "eventTime": globalClock.getFrameTime(),
                "source": self,
                "sequence": info.channel,
                "cycle": event.getCycle(),
                "event": event.getEvent(),
                "options": event.getOptions(),
                "type": event.getType()}
            handler.handleAnimEvent(eventInfo)

    def SendProxy_animLayers(self):
        layers = []
        for i in range(self.character.getNumAnimLayers() - 1):
            layer = self.character.getAnimLayer(i + 1)
            layers.append(
                (layer._play_mode,
                 layer._start_cycle,
                 layer._play_cycles,
                 layer._cycle,
                 layer._prev_cycle,
                 layer._weight,
                 layer._order,
                 layer._sequence,
                 layer._sequence_parity))
        return layers

    def setModel(self, filename):
        self.loadModel(filename)

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

            #print("layers", self.character.getNumAnimLayers())
            #print("seq", self.getCurrSequence())
            #print("pr", self.getPlayRate())

        self.animTime = globalClock.getFrameTime()

    def getAnimTime(self):
        return self.animTime

    def setAnimTime(self, time):
        self.animTime = time

    def SendProxy_animTime(self):
        tickNumber = base.timeToTicks(self.getAnimTime())
        tickBase = base.getNetworkBase(base.tickCount, self.doId)
        addT = 0
        if tickNumber >= (tickBase - 100):
            addT = (tickNumber - tickBase) & 0xFF

        return addT

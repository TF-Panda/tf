
from tf.entity.DistributedEntity import DistributedEntityAI
from .Char import Char

from .AnimEvents import AnimEventType

class DistributedCharAI(DistributedEntityAI, Char):

    def __init__(self):
        DistributedEntityAI.__init__(self)
        Char.__init__(self)

        self.lastEventCheck = 0.0

    def dispatchAnimEvents(self, handler):
        if not self.seqPlayer:
            return

        if self.seqPlayer.getPlayRate() == 0.0:
            return

        seqIdx = self.getCurrSequence()
        if seqIdx == -1:
            return

        seq = self.getSequence(seqIdx)
        if seq.getNumEvents() == 0:
            return

        # Look from when it last checked to some short time in the future.
        cycleRate = self.seqPlayer.getSequenceCycleRate(seqIdx) * self.seqPlayer.getPlayRate()
        start = self.lastEventCheck
        end = self.seqPlayer.getCycle()

        if not self.seqPlayer.isSequenceLooping() and self.seqPlayer.isSequenceFinished():
            end = 1.0

        self.lastEventCheck = end

        for i in range(seq.getNumEvents()):
            event = seq.getEvent(i)

            if (event.getType() & AnimEventType.Server) == 0:
                # Not a server event.
                continue

            overlap = False
            if event.getCycle() >= start and event.getCycle() < end:
                overlap = True
            elif seq.hasFlags(AnimSequence.FLooping) and end < start:
                if event.getCycle() >= start and event.getCycle() < end:
                    overlap = True

            if overlap:
                eventInfo = {
                    "eventTime": globalClock.getFrameTime(),
                    "source": self,
                    "sequence": seqIdx,
                    "cycle": event.getCycle(),
                    "event": event.getEvent(),
                    "options": event.getOptions(),
                    "type": event.getType()}

                # Calculate when this event should happen.
                if cycleRate > 0.0:
                    cycle = event.getCycle()
                    if cycle > self.getCycle():
                        cycle = cycle - 1.0
                    eventInfo["eventTime"] = self.getAnimTime() + (cycle - self.getCycle()) / cycleRate + self.seqPlayer.getAnimTimeInterval()

                handler.handleAnimEvent(eventInfo)

    def SendProxy_newSequenceParity(self):
        return self.seqPlayer.getNewSequenceParity()

    def SendProxy_sequence(self):
        curr = self.seqPlayer.getCurrSequence()
        return curr

    def SendProxy_cycle(self):
        cycle =  self.seqPlayer.getCycle()
        return cycle

    def SendProxy_playRate(self):
        pr =  self.seqPlayer.getPlayRate()
        return pr

    def SendProxy_animLayers(self):
        layers = []
        for i in range(self.seqPlayer.getNumLayers()):
            layer = self.seqPlayer.getLayer(i)
            layers.append((layer._sequence, layer._cycle, layer._prev_cycle, layer._weight, layer._order, layer._sequence_parity))
        return layers

    def setModel(self, filename):
        self.loadModel(filename)

    def loadModel(self, model):
        Char.loadModel(self, model)
        self.modelNp.reparentTo(self)
        if self.seqPlayer:
            # The server doesn't blend sequence transitions.
            self.seqPlayer.setTransitionsEnabled(False)

        self.ls()

    def simulate(self):
        DistributedEntityAI.simulate(self)

        if self.character:
            # Compute the animation.   This also advances the anim time and
            # cycle on the sequence player, which will be sent to clients.
            self.character.update()

    def SendProxy_animTime(self):
        tickNumber = base.timeToTicks(self.seqPlayer.getAnimTime())
        tickBase = base.getNetworkBase(base.tickCount, self.doId)
        addT = 0
        if tickNumber >= (tickBase - 100):
            addT = (tickNumber - tickBase) & 0xFF

        return addT

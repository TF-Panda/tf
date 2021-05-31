
from tf.entity.DistributedEntity import DistributedEntity
from .Char import Char

from panda3d.core import *
from panda3d.direct import *

class DistributedChar(DistributedEntity, Char):

    def __init__(self):
        DistributedEntity.__init__(self)
        Char.__init__(self)
        self.lastSequence = -1
        self.oldAnimTime = 0.0

        self.ivCycle = InterpolatedFloat()
        self.addInterpolatedVar(self.ivCycle, self.getCycle, self.setCycle, self.AnimationVar)

        self.animLayerIvs = []

    def getLayerIV(self, layer):
        """
        Returns a representation of the indicated anim layer for use with
        interpolation.
        """
        return ClientAnimLayer(self.seqPlayer.getLayer(layer))

    def setLayerIV(self, index, layerData):
        """
        Applies the interpolated anim layer data to the physical anim layer.
        """
        layer = self.seqPlayer.getLayer(index)
        layer._sequence = layerData.sequence
        layer._order = layerData.order
        layer._cycle = layerData.cycle
        layer._prev_cycle = layerData.prev_cycle
        layer._weight = layerData.weight
        layer._sequence_parity = layerData.sequence_parity
        if layer._order != 15:
            layer._flags |= AnimLayer.F_active
        else:
            layer._flags &= ~AnimLayer.F_active

    def addLayerIVs(self, startIndex, count):
        for i in range(startIndex, startIndex + count):
            ivLayer = InterpolatedClientAnimLayer()
            self.addInterpolatedVar(ivLayer, self.getLayerIV, self.setLayerIV, self.AnimationVar, i)
            self.animLayerIvs.append(ivLayer)

    def removeLayerIVs(self, startIndex, count):
        removeLayers = self.animLayerIvs[startIndex : startIndex + count]

        for rem in removeLayers:
            self.animLayerIvs.remove(rem)
            self.removeInterpolatedVar(rem)

    def RecvProxy_animLayers(self, layers):
        oldCount = len(self.animLayerIvs)
        count = len(layers)
        diff = count - oldCount

        if diff != 0:
            self.seqPlayer.setNumLayers(count)

            startIndex = oldCount
            if diff > 0:
                self.addLayerIVs(startIndex, diff)
            else:
                self.removeLayerIVs(startIndex, -diff)

        for i in range(count):
            layerData = layers[i]
            layer = self.seqPlayer.getLayer(i)
            layer._sequence = layerData[0]
            layer._cycle = layerData[1]
            layer._prev_cycle = layerData[2]
            layer._weight = layerData[3]
            layer._order = layerData[4]
            layer._sequence_parity = layerData[5]
            if layer._order != 15:
                layer._flags |= AnimLayer.F_active
            else:
                layer._flags &= ~AnimLayer.F_active

    def checkForLayerChanges(self, now):
        layersChanged = False
        info = InterpolationInfo()
        # FIXME: damn, there has to be a better way to do this.
        for i in range(self.seqPlayer.getNumLayers()):
            self.animLayerIvs[i].getInterpolationInfo(info, now)
            ihead = info.newer
            iprev1 = info.older
            iprev2 = info.oldest
            head = self.animLayerIvs[i].getSampleValue(ihead)
            t0 = self.animLayerIvs[i].getSampleTimestamp(ihead)
            prev1 = self.animLayerIvs[i].getSampleValue(iprev1)
            t1 = self.animLayerIvs[i].getSampleTimestamp(iprev1)
            prev2 = self.animLayerIvs[i].getSampleValue(iprev2)
            t2 = self.animLayerIvs[i].getSampleTimestamp(iprev2)

            if (head is not None) and (prev1 is not None) and \
                ((head.sequence != prev1.sequence) or (head.sequence_parity != prev1.sequence_parity)):

                # Sequence changed!
                layersChanged = True

                looping = self.getSequence(head.sequence).hasFlags(AnimSequence.FLooping)

                if prev1 is not None:
                    prev1.sequence = head.sequence
                    prev1.sequence_parity = head.sequence_parity
                    prev1.cycle = head.prev_cycle
                    prev1.weight = head.weight

                if prev2 is not None:
                    num = 0
                    if abs(t0 - t1) > 0.001:
                        num = (t2 - t1) / (t0 - t1)
                    if looping:
                        prev2.cycle = LoopingLerp(num, head.prev_cycle, head.cycle)
                    else:
                        prev2.cycle = flerp(head.prev_cycle, head.cycle, num)
                    prev2.sequence = head.sequence
                    prev2.sequence_parity = head.sequence_parity
                    prev2.weight = head.weight

                self.animLayerIvs[i].setLooping(looping)
                self.animLayerIvs[i].interpolate(now)
                self.setLayerIV(i, self.animLayerIvs[i].getInterpolatedValue())

    def checkForLayerChangesTask(self, task):
        self.checkForLayerChanges(globalClock.getFrameTime())
        return task.cont

    def RecvProxy_newSequenceParity(self, parity):
        self.seqPlayer.setNewSequenceParity(parity)

    def getLastChangedTime(self, flags):
        if flags & self.AnimationVar:
            return self.getAnimTime()

        return DistributedEntity.getLastChangedTime(self, flags)

    def postInterpolate(self):
        DistributedEntity.postInterpolate(self)
        if globalClock.getDt() != 0.0:
            self.doAnimationEvents()

    def postDataUpdate(self):
        DistributedEntity.postDataUpdate(self)

        # Check for anim time change to latch animation vars.
        animTimeChanged = self.getAnimTime() != self.oldAnimTime
        if (not self.isPredictable()) and animTimeChanged:
            self.onLatchInterpolatedVars(
                self.getLastChangedTime(self.AnimationVar),
                self.AnimationVar)
        self.oldAnimTime = self.getAnimTime()

        # Reset the cycle interpolation if we have a new sequence.
        if self.seqPlayer.getNewSequenceParity() != self.seqPlayer.getPrevSequenceParity():
            self.ivCycle.reset(self.getCycle())
            if self.getCurrSequence() != -1:
                self.ivCycle.setLooping(self.getSequence(self.getCurrSequence()).hasFlags(AnimSequence.FLooping))

    def setCycle(self, cycle):
        self.seqPlayer.setCycle(cycle)

    def getCycle(self):
        return self.seqPlayer.getCycle()

    def RecvProxy_cycle(self, cycle):
        self.seqPlayer.setCycle(cycle)

    def RecvProxy_playRate(self, rate):
        self.seqPlayer.setPlayRate(rate)

    def RecvProxy_sequence(self, seq):
        self.seqPlayer.setSequence(seq)

    def RecvProxy_model(self, modelFilename):
        self.loadModel(modelFilename)

    def loadModel(self, model):
        Char.loadModel(self, model)
        self.modelNp.reparentTo(self)
        if self.seqPlayer:
            # The client receives anim time and cycle from the server, so
            # the player should not advance for him.
            self.seqPlayer.setAdvanceMode(AnimSequencePlayer.AMManual)

    def RecvProxy_sequence(self, seq):
        # Start the sequence playing.
        self.setSequence(seq)

    def generate(self):
        DistributedEntity.generate(self)
        self.addTask(self.checkForLayerChangesTask, "checkForLayerChanges", sim = False, appendTask = True, sort = 37)

    def disable(self):
        self.clearModel()
        self.animLayerIvs = None
        self.ivCycle = None
        DistributedEntity.disable(self)

    def RecvProxy_animTime(self, addT):
        tickBase = base.getNetworkBase(base.tickCount, self.doId)
        t = tickBase
        t += addT

        while t < base.tickCount - 127:
            t += 256
        while t > base.tickCount + 127:
            t -= 256

        self.seqPlayer.setAnimTime(t * base.intervalPerTick)

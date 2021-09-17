
from tf.entity.DistributedEntity import DistributedEntity
from .Char import Char

from tf.tfbase.TFGlobals import SolidShape

from panda3d.core import *
from panda3d.direct import *

class DistributedChar(Char, DistributedEntity):

    def __init__(self):
        Char.__init__(self)
        DistributedEntity.__init__(self)
        self.oldAnimTime = 0.0
        self.animTime = 0.0

        # Client-side ragdoll associated with this entity.
        self.ragdoll = None

        self.clientSideAnimation = False

        self.addPredictionField("skin", int, setter=self.setSkin)
        #self.addPredictionField("sequence", int, setter=self.setSequence,
        #                        getter=self.getCurrSequence, noErrorCheck=True)
        #self.addPredictionField("playRate", float, setter=self.setPlayRate,
        #                        getter=self.getPlayRate, noErrorCheck=True)
        #self.addPredictionField("cycle", float, setter=self.setCycle,
        #                        getter=self.getCycle, noErrorCheck=True)
        #self.addPredictionField("playMode", int, setter=self.setPlayMode,
        #                        getter=self.getPlayMode, noErrorCheck=True)
        #self.addPredictionField("startCycle", float, setter=self.setPlayMode,
        #                        getter=self.getPlayMode, noErrorCheck=True)
        #self.addPredictionField("playCycles", float, setter=self.setPlayMode,
        #                        getter=self.getPlayMode, noErrorCheck=True)
        #self.addPredictionField("animTime", float, getter=self.getAnimTime, setter=self.setAnimTime,
        #                        tolerance=0.001, noErrorCheck=True)
        #self.addPredictionField("newSequenceParity", int, getter=self.getNewSequenceParity,
        #                        setter=self.setNewSequenceParity, noErrorCheck=True)
        #self.addPredictionField("prevAnimTime", float, networked=False)

        self.animLayerIvs = []

        self.ivCycle = InterpolatedFloat()
        self.addInterpolatedVar(self.ivCycle, self.getCycle, self.setCycle, self.SimulationVar)
        self.ivCycleAdded = True

    def RecvProxy_sequence(self, seq):
        if self.clientSideAnimation:
            return
        self.setSequence(seq)

    def RecvProxy_cycle(self, cycle):
        if self.clientSideAnimation:
            return
        self.setCycle(cycle)

    def RecvProxy_playRate(self, rate):
        if self.clientSideAnimation:
            return
        self.setPlayRate(rate)

    def RecvProxy_newSequenceParity(self, parity):
        if self.clientSideAnimation:
            return
        self.setNewSequenceParity(parity)

    def setPlayMode(self, mode):
        if not self.character:
            return
        layer = self.character.getAnimLayer(0)
        layer._play_mode = int(mode)

    def getPlayMode(self):
        if not self.character:
            return 0
        return int(self.character.getAnimLayer(0)._play_mode)

    def RecvProxy_playMode(self, mode):
        if self.clientSideAnimation:
            return
        self.setPlayMode(mode)

    def RecvProxy_startCycle(self, cycle):
        if self.clientSideAnimation:
            return
        self.setStartCycle(cycle)

    def setStartCycle(self, cycle):
        if not self.character:
            return
        layer = self.character.getAnimLayer(0)
        layer._start_cycle = cycle

    def getStartCycle(self):
        if not self.character:
            return 0.0
        return float(self.character.getAnimLayer(0)._start_cycle)

    def RecvProxy_playCycles(self, cycles):
        if self.clientSideAnimation:
            return
        self.setPlayCycles(cycles)

    def setPlayCycles(self, cycles):
        if not self.character:
            return
        layer = self.character.getAnimLayer(0)
        layer._play_cycles = cycles

    def getPlayCycles(self):
        if not self.character:
            return 0.0
        return float(self.character.getAnimLayer(0)._play_cycles)

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

        DistributedEntity.initializeCollisions(self)

    def makeModelCollisionShape(self):
        return Char.makeModelCollisionShape(self)

    def onModelChanged(self):
        self.initializeCollisions()
        Char.onModelChanged(self)

    def becomeRagdoll(self, forceJoint, forcePosition, forceVector):
        self.ragdoll = Char.becomeRagdoll(self, forceJoint, forcePosition, forceVector)
        return self.ragdoll

    def RecvProxy_clientSideAnimation(self, flag):
        self.setClientSideAnimation(flag)

    def setClientSideAnimation(self, flag):
        if flag == self.clientSideAnimation:
            return
        self.clientSideAnimation = flag
        self.updateClientSideAnimation()

    def updateClientSideAnimation(self):
        if self.clientSideAnimation:
            # Client should drive the animation.
            self.setAutoAdvance(True)
        else:
            self.setAutoAdvance(False)

        if self.clientSideAnimation and self.ivCycleAdded:
            # Don't interpolate cycle.
            self.removeInterpolatedVar(self.ivCycle)
            self.ivCycleAdded = False
        elif not self.clientSideAnimation and not self.ivCycleAdded:
            self.addInterpolatedVar(self.ivCycle, self.getCycle, self.setCycle, self.SimulationVar)
            self.ivCycleAdded = True

    def RecvProxy_skin(self, skin):
        self.setSkin(skin)

    def getLayerIV(self, n):
        """
        Returns a representation of the indicated anim layer for use with
        interpolation.
        """
        layer = self.character.getAnimLayer(n + 1)
        if layer:
            return ClientAnimLayer(layer)
        else:
            return ClientAnimLayer(AnimLayer())

    def setLayerIV(self, index, layerData):
        """
        Applies the interpolated anim layer data to the physical anim layer.
        """
        layer = self.character.getAnimLayer(index + 1)
        if not layer:
            return
        layer._play_mode = layerData.play_mode
        layer._start_cycle = layerData.start_cycle
        layer._play_cycles = layerData.play_cycles
        layer._sequence = layerData.sequence
        layer._order = layerData.order
        layer._cycle = layerData.cycle
        layer._prev_cycle = layerData.prev_cycle
        layer._weight = layerData.weight
        layer._sequence_parity = layerData.sequence_parity
        if layer._order >= 0:
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
        if self.clientSideAnimation:
            return

        oldCount = len(self.animLayerIvs)
        count = len(layers)
        diff = count - oldCount

        if diff != 0:
            self.character.ensureLayerCount(count + 1)

            startIndex = oldCount
            if diff > 0:
                self.addLayerIVs(startIndex, diff)
            else:
                startIndex += diff
                self.removeLayerIVs(startIndex, -diff)

        for i in range(count):
            layerData = layers[i]
            layer = self.character.getAnimLayer(i + 1)
            if not layer:
                continue

            layer._play_mode = layerData[0]
            layer._start_cycle = layerData[1]
            layer._play_cycles = layerData[2]
            layer._cycle = layerData[3]
            layer._prev_cycle = layerData[4]
            layer._weight = layerData[5]
            layer._order = layerData[6]
            layer._sequence = layerData[7]
            layer._sequence_parity = layerData[8]
            if layer._order >= 0:
                layer._flags |= AnimLayer.F_active
            else:
                layer._flags &= ~AnimLayer.F_active

    def checkForLayerChanges(self, now):
        if self.clientSideAnimation:
            return

        layersChanged = False
        info = InterpolationInfo()
        # FIXME: damn, there has to be a better way to do this.
        for i in range(self.character.getNumAnimLayers() - 1):
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

                looping = False
                if head.sequence >= 0:
                    looping = self.character.getChannel(head.sequence).hasFlags(AnimChannel.FLooping)

                if prev1 is not None:
                    prev1.sequence = head.sequence
                    prev1.sequence_parity = head.sequence_parity
                    prev1.cycle = head.prev_cycle
                    prev1.weight = head.weight
                    prev1.play_mode = head.play_mode
                    prev1.start_cycle = head.start_cycle
                    prev1.play_cycles = head.play_cycles

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
                    prev2.play_mode = head.play_mode
                    prev2.start_cycle = head.start_cycle
                    prev2.play_cycles = head.play_cycles

                self.animLayerIvs[i].setLooping(looping)
                self.animLayerIvs[i].interpolate(now)
                self.setLayerIV(i, self.animLayerIvs[i].getInterpolatedValue())

    def checkForLayerChangesTask(self, task):
        self.checkForLayerChanges(globalClock.getFrameTime())
        return task.cont

    def getAnimTime(self):
        return self.animTime

    def setAnimTime(self, time):
        self.animTime = time

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
        if (not self.getPredictable()) and animTimeChanged:
            self.onLatchInterpolatedVars(
                self.getLastChangedTime(self.AnimationVar),
                self.AnimationVar)
        self.oldAnimTime = float(self.getAnimTime())

        # Reset the cycle interpolation if we have a new sequence.
        if self.getNewSequenceParity() != self.getPrevSequenceParity() and not self.clientSideAnimation:
            # Manually reset for client-side animation.
            #if self.clientSideAnimation:
            #    self.setCycle(0.0)

            self.ivCycle.reset(self.getCycle())
            if self.getCurrSequence() != -1:
                self.ivCycle.setLooping(self.character.getChannel(self.getCurrSequence()).hasFlags(AnimChannel.FLooping))

        self.updateClientSideAnimation()

    def RecvProxy_model(self, modelFilename):
        self.loadModel(modelFilename)

    def loadModel(self, model):
        Char.loadModel(self, model)
        self.updateClientSideAnimation()

    def simulate(self):
        DistributedEntity.simulate(self)
        # If we're predicting and not using client-side animation, predict the
        # animation time and cycle.
        if self.predictable and not self.clientSideAnimation:
            self.character.advance()
            self.animTime = globalClock.getFrameTime()

    def generate(self):
        DistributedEntity.generate(self)
        self.addTask(self.checkForLayerChangesTask, "checkForLayerChanges", sim = False, appendTask = True, sort = 37)

    def disable(self):
        self.clearModel()
        self.ivCycle = None
        self.animLayerIvs = None
        DistributedEntity.disable(self)

    def delete(self):
        self.cleanup()
        DistributedEntity.delete(self)

    def RecvProxy_animTime(self, addT):
        # Ignore for client-side animation.
        if self.clientSideAnimation:
            return

        tickBase = base.getNetworkBase(base.tickCount, self.doId)
        t = tickBase
        t += addT

        while t < base.tickCount - 127:
            t += 256
        while t > base.tickCount + 127:
            t -= 256

        self.setAnimTime(t * base.intervalPerTick)

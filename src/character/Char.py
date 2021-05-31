
from panda3d.core import *
from panda3d.pphysics import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from .Activity import Activity
from .AnimEvents import AnimEvent, AnimEventType
from .HitBox import HitBox
from tf.tfbase.Sounds import createSound
from tf.tfbase.TFGlobals import CollisionGroup, Contents

from .ModelDefs import ModelDefs

Ragdolls = []

class Char:
    notify = directNotify.newCategory("Char")

    def __init__(self):
        self.modelNp = None
        self.characterNp = None
        self.character = None
        self.anims = {}
        self.hitBoxes = []
        # Filename of the model.
        self.model = ""

        self.resetEventsParity = 0
        self.prevResetEventsParity = 0
        self.prevEventCycle = -0.01
        self.lastEventSequence = -1

        self.lastHitBoxSyncTime = 0.0

        self.seqPlayer = None

    def getModelNode(self):
        return self.modelNp

    def getCharacterNode(self):
        return self.characterNp

    def becomeRagdoll(self, forceJoint, forcePosition, forceVector):
        modelDef = ModelDefs[self.model]
        if not hasattr(modelDef, 'createRagdoll'):
            # Model doesn't have a ragdoll.
            return

        # Hide ourselves.
        self.modelNp.hide()

        cCopy = Char()
        cCopy.loadModel(self.model)
        cCopy.modelNp.node().setBounds(OmniBoundingVolume())
        # Copy the current joint positions of our character to the ragdoll
        # version.
        for i in range(self.character.getNumJoints()):
            cCopy.character.setJointForcedValue(i, self.character.getJointValue(i))
        cCopy.modelNp.reparentTo(render)
        cCopy.modelNp.setTransform(self.modelNp.getNetTransform())
        rd = modelDef.createRagdoll(cCopy)
        rd.setup()
        if forceJoint == -1:
            rd.setEnabled(True)
        else:
            rd.setEnabled(True, cCopy.character.getJointName(forceJoint), forceVector, forcePosition)
        Ragdolls.append((cCopy, rd))

        return (cCopy, rd)

        #self.resetSequence(-1)

    def setupHitBoxes(self):
        modelDef = ModelDefs[self.model]
        if hasattr(modelDef, 'createHitBoxes'):
            modelDef.createHitBoxes(self)

    def addHitBox(self, group, jointName, mins, maxs):
        joint = self.character.findJoint(jointName)
        if joint == -1:
            self.notify.warning(f"addHitBox(): joint {jointName} not found on character {self.character.getName()}")
            return

        hX = (maxs[0] - mins[0]) / 2
        hY = (maxs[1] - mins[1]) / 2
        hZ = (maxs[2] - mins[2]) / 2
        cX = (maxs[0] + mins[0]) / 2
        cY = (maxs[1] + mins[1]) / 2
        cZ = (maxs[2] + mins[2]) / 2
        box = PhysBox(hX, hY, hZ)
        # Even though hit boxes are scene query shapes, they still need a
        # material.  Just give it a bogus one.
        mat = PhysMaterial(0, 0, 0)
        shape = PhysShape(box, mat)
        shape.setLocalPos((cX, cY, cZ))
        shape.setSimulationShape(False)
        shape.setTriggerShape(False)
        shape.setSceneQueryShape(True)
        body = PhysRigidDynamicNode("hbox_" + self.character.getName() + "_" + jointName)
        body.setContentsMask(Contents.HitBox)
        body.addShape(shape)
        body.setKinematic(True)
        body.addToScene(base.physicsWorld)
        hbox = HitBox(group, body, joint)
        # Add a link to ourself so traces know who they hit.
        body.setPythonTag("hitbox", (self, hbox))
        self.characterNp.attachNewNode(body)
        self.hitBoxes.append(hbox)

    def getNumHitBoxes(self):
        return len(self.hitBoxes)

    def getHitBox(self, n):
        return self.hitBoxes[n]

    def syncHitBoxes(self):
        """
        Synchronizes the physics bodies of character's hit boxes with the
        current world-space transform of the associated joints.
        """

        now = globalClock.getFrameTime()
        if now == self.lastHitBoxSyncTime:
            # We're already synchronized with the current point in time.
            return

        self.lastHitBoxSyncTime = now

        for hbox in self.hitBoxes:
            joint = hbox.joint
            body = hbox.body
            body.setTransform(TransformState.makeMat(self.character.getJointNetTransform(joint)))

    def doAnimationEvents(self):
        if self.getCurrSequence() == -1:
            return

        watch = False

        eventCycle = self.getCycle()

        # Assume we're visible if render or viewmodel render is the top of our
        # hierarchy.  FIXME: better solution for this
        top = self.modelNp.getTop()
        visible = (top in [render, base.vmRender])
        if not visible:
            return

        seqIdx = self.getCurrSequence()
        seq = self.getSequence(seqIdx)

        resetEvents = seqIdx != self.lastEventSequence#self.resetEventsParity != self.prevResetEventsParity
        self.lastEventSequence = seqIdx
        self.prevResetEventsParity = self.resetEventsParity

        if resetEvents:
            if watch:
                print(f"new seq: {seqIdx} - old seq: {self.lastEventSequence} - reset: {resetEvents} - cycle: {self.getCycle()} - (time {globalClock.getFrameTime()})")
            eventCycle = 0.0
            self.prevEventCycle = -0.01
            self.lastEventSequence = seqIdx

        if eventCycle == self.prevEventCycle:
            return

        if watch:
            print(f"{base.tickCount} (seq {seqIdx} cycle {self.getCycle()}) evcycle {eventCycle} prevevcycle {self.prevEventCycle} (time {globalClock.getFrameTime()})")

        looped = False
        if eventCycle <= self.prevEventCycle:
            if self.prevEventCycle - eventCycle > 0.5:
                looped = True
            else:
                return

        if looped:
            for i in range(seq.getNumEvents()):
                event = seq.getEvent(i)

                if (event.getType() & AnimEventType.Client) == 0:
                    # Not a client event.
                    continue

                if event.getCycle() <= self.prevEventCycle:
                    continue

                if watch:
                    print(f"{base.tickCount} FE {event.getEvent()} Looped cycle {event.getCycle()}, prev {self.prevEventCycle} ev {eventCycle} (time {globalClock.getFrameTime()})")

                self.fireEvent(self.modelNp.getPos(render), self.modelNp.getHpr(render), event.getEvent(), event.getOptions())

            self.prevEventCycle = -0.01

        for i in range(seq.getNumEvents()):
            event = seq.getEvent(i)

            if (event.getType() & AnimEventType.Client) == 0:
                # Not a client event.
                continue

            if event.getCycle() > self.prevEventCycle and event.getCycle() <= eventCycle:
                if watch:
                    print(f"{base.tickCount} (seq: {seqIdx}) FE {event.getEvent()} Normal cycle {event.getCycle()}, prev {self.prevEventCycle} ev {eventCycle} (time {globalClock.getFrameTime()})")
                self.fireEvent(self.modelNp.getPos(render), self.modelNp.getHpr(render), event.getEvent(), event.getOptions())

        self.prevEventCycle = eventCycle

    def fireEvent(self, pos, angles, event, options):
        if event == AnimEvent.Client_Play_Sound:
            soundName = options
            sound = createSound(soundName)
            if not sound:
                return
            sound.set3dAttributes(pos[0], pos[1], pos[2], 0, 0, 0)
            sound.play()

    def getCycle(self):
        return self.seqPlayer.getCycle()

    def getAnimTime(self):
        return self.seqPlayer.getAnimTime()

    def getCurrSequence(self):
        return self.seqPlayer.getCurrSequence()

    def addSequence(self, seq):
        return self.character.addSequence(seq)

    def getNumSequences(self):
        return self.character.getNumSequences()

    def getSequence(self, n):
        return self.character.getSequence(n)

    def getNumAnims(self):
        return self.character.getNumAnims()

    def getAnim(self, n):
        return self.character.getAnim(n)

    def createSimpleSequence(self, animName, activity, looping, snap = False):
        seq = AnimSequence(animName, self.anims[animName])
        seq.setActivity(activity)
        if looping:
            seq.setFlags(AnimSequence.FLooping)
        if snap:
            seq.setFlags(AnimSequence.FSnap)
        return seq

    def getSequenceActivity(self, sequence):
        if isinstance(sequence, str):
            sequence = self.findSequence(name)
        if sequence == -1:
            return Activity.Invalid
        return self.getSequence(sequence).getActivity()

    def getSequenceForActivity(self, activity):
        return self.character.getSequenceForActivity(activity, self.getCurrSequence())

    def getSequencesForActivity(self, activity):
        seqs = []
        for i in range(self.getNumSequences()):
            seq = self.getSequence(i)
            if seq.getActivity() == activity:
                seqs.append(i)

        return seqs

    def findSequence(self, name):
        for i in range(self.getNumSequences()):
            if self.getSequence(i).getName() == name:
                return i

        return -1

    def getSequenceLength(self, seq):
        if isinstance(seq, str):
            seqIdx = self.findSequence(seq)
        else:
            seqIdx = seq
        if seqIdx == -1:
            return 0.0

        return self.getSequence(seqIdx).getLength()

    def setSequence(self, seq):
        if isinstance(seq, str):
            self.sequence = self.findSequence(seq)
        else:
            self.sequence = seq
        if self.seqPlayer:
            self.seqPlayer.setSequence(self.sequence)
            #self.seqPlayer.setCycle(0.0)

    def resetSequence(self, seq):
        if isinstance(seq, str):
            self.sequence = self.findSequence(seq)
        else:
            self.sequence = seq
        if self.seqPlayer:
            self.seqPlayer.resetSequence(self.sequence)

    def restartGesture(self, act):
        if self.seqPlayer:
            self.seqPlayer.restartGesture(act)

    def isCurrentSequenceFinished(self):
        return self.seqPlayer.isSequenceFinished()

    def isCurrentSequenceLooping(self):
        return self.seqPlayer.isSequenceLooping()

    def setupSequences(self):
        # Terrible temporary kludge to set up sequences from the model
        # filename.
        modelDef = ModelDefs[self.model]
        if hasattr(modelDef, 'createSequences'):
            modelDef.createSequences(self)

    def setupGestures(self):
        pass

    def setupPoseParameters(self):
        modelDef = ModelDefs[self.model]
        if hasattr(modelDef, 'createPoseParameters'):
            modelDef.createPoseParameters(self)

    def addPoseParameter(self, name, minVal, maxVal, looping = False):
        return self.character.addPoseParameter(name, minVal, maxVal, looping)

    def findPoseParameter(self, name):
        return self.character.findPoseParameter(name)

    def getPoseParameter(self, name):
        if isinstance(name, str):
            idx = self.character.findPoseParameter(name)
            if idx == -1:
                return None
            return self.character.getPoseParameter(idx)
        else:
            return self.character.getPoseParameter(name)

    def setAnimGraph(self, graph):
        self.character.setAnimGraph(graph)

    def getAnimGraph(self):
        return self.character.getAnimGraph()

    def getCharacter(self):
        return self.character

    def getAnim(self, name):
        return self.anims.get(name, None)

    def setJointMergeCharacter(self, char):
        self.character.setJointMergeCharacter(char)

    def getJointMergeCharacter(self):
        return self.character.getJointMergeCharacter()

    def setJointMerge(self, jointName, enable = True):
        jointIdx = self.character.findJoint(jointName)
        if jointIdx == -1:
            return
        self.character.setJointMerge(jointIdx, enable)

    def getJointMerge(self, jointName):
        jointIdx = self.character.findJoint(jointName)
        if jointIdx == -1:
            return
        self.character.getJointMerge(jointIdx)

    def clearModel(self):
        self.model = ""
        # Just dropping the references to the hit boxes is good enough to free
        # them from both the physics world and memory.
        self.hitBoxes = []
        self.lastHitBoxSyncTime = 0.0
        self.gestures = []
        self.anims = {}
        if self.modelNp:
            self.modelNp.removeNode()
            self.modelNp = None
        self.characterNp = None
        self.character = None
        self.animFSM = None
        self.animOverlay = None

    def loadAnims(self, anims):
        if not self.character:
            return

        for name, filename in anims.items():
            animModelNp = base.loader.loadModel(filename)
            animBundleNp = animModelNp.find("**/+AnimBundleNode")
            if animBundleNp.isEmpty():
                continue
            animBundle = animBundleNp.node().getBundle()
            index = self.character.bindAnim(
              animBundle)
            if index != -1:
                self.anims[name] = control

    def onModelChanged(self):
        pass

    def loadModel(self, model):
        if self.model == model:
            return

        self.clearModel()

        self.model = model

        if len(model) == 0:
            return

        self.modelNp = base.loader.loadModel(model)
        if self.modelNp.isEmpty():
            self.notify.error("Failed to load model", model)
            return
        # We don't need to consider culling past the root of the model.
        self.modelNp.node().setFinal(True)

        self.characterNp = self.modelNp.find("**/+CharacterNode")
        if self.characterNp.isEmpty():
            self.notify.error("Model", model, "does not contain a CharacterNode!")
            return

        self.character = self.characterNp.node().getCharacter()
        self.character.setFrameBlendFlag(True)

        # Now go through each AnimBundle that was embedded in the model and
        # bind 'em.
        animBundleNodes = self.modelNp.findAllMatches("**/+AnimBundleNode")
        for animBundleNode in animBundleNodes:
            animBundle = animBundleNode.node().getBundle()
            index = self.character.bindAnim(animBundle)
            if index != -1:
                self.anims[animBundleNode.getName()] = self.character.getAnim(index)

        self.seqPlayer = AnimSequencePlayer("player", self.character)
        self.character.setAnimGraph(self.seqPlayer)

        self.setupHitBoxes()
        self.setupPoseParameters()
        self.setupSequences()
        #self.setupGestures()

        #if self.sequence != -1:
        #    self.setSequence(self.sequence)

        self.onModelChanged()


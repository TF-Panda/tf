
from panda3d.core import *
from panda3d.pphysics import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.actor.Actor import Actor
from .Activity import Activity
from .AnimEvents import AnimEvent, AnimEventType
from .HitBox import HitBox
from tf.tfbase.Sounds import Sounds, createSoundByName
from tf.tfbase.TFGlobals import CollisionGroup, Contents

from .ModelDefs import ModelDefs

Ragdolls = []

class Char(Actor):
    notify = directNotify.newCategory("Char")

    def __init__(self):
        Actor.__init__(self, flattenable=1, setFinal=1)

        self.character = None
        self.characterNp = None
        self.modelNp = None
        self.hullNp = None
        self.collAttached = False
        self.anims = {}
        self.hitBoxes = []
        self.soundsByChannel = {}
        self.bodygroups = {}
        # Filename of the model.
        self.model = ""

        self.resetEventsParity = 0
        self.prevResetEventsParity = 0
        self.prevEventCycle = -0.01
        self.lastEventSequence = -1

        self.lastHitBoxSyncTime = 0.0

        self.skin = 0

    def setBodygroupValue(self, group, value):
        bg = self.bodygroups[group]
        for i in range(len(bg)):
            body = bg[i]
            if i == value:
                body.show()
            else:
                body.hide()

    def setSkin(self, skin):
        self.skin = skin
        self.updateModelSkin()

    def updateModelSkin(self):
        modelNp = self.getPartModel()

        if not modelNp:
            return

        modelNode = modelNp.node()
        if isinstance(modelNode, ModelRoot):
            if self.skin >= 0 and self.skin < modelNode.getNumMaterialGroups():
                modelNode.setActiveMaterialGroup(self.skin)

    def getSkin(self):
        return self.skin

    def getModelNode(self):
        return self.modelNp

    def getCharacterNode(self):
        return self.characterNp

    def becomeRagdoll(self, forceJoint, forcePosition, forceVector):
        forceVector = Vec3(forceVector[0], forceVector[1], forceVector[2])
        forcePosition = Point3(forcePosition[0], forcePosition[1], forcePosition[2])

        if not self.model in ModelDefs:
            return None

        modelDef = ModelDefs[self.model]
        if not hasattr(modelDef, 'createRagdoll'):
            # Model doesn't have a ragdoll.
            return None

        # Hide ourselves.
        self.hide()

        # Make sure the joints reflect the current animation in case we were
        # hidden or off-screen.
        Actor.update(self)

        cCopy = Char()
        cCopy.setSkin(self.skin)
        cCopy.loadModel(self.model)
        cCopy.node().setBounds(OmniBoundingVolume())
        # Copy the current joint positions of our character to the ragdoll
        # version.
        character = self.getPartBundle("modelRoot")
        cCharacter = cCopy.getPartBundle("modelRoot")
        for i in range(character.getNumJoints()):
            cCharacter.setJointForcedValue(i, character.getJointValue(i))
        cCopy.reparentTo(render)
        cCopy.setTransform(self.getNetTransform())
        rd = modelDef.createRagdoll(cCopy)
        rd.setup()
        if forceJoint == -1:
            rd.setEnabled(True, "bip_pelvis", forceVector, forcePosition)
        else:
            # Find the closest joint to apply the force to.
            joint = forceJoint
            jointName = ""
            foundJoint = False
            while not foundJoint and joint != -1:
                jointName = cCopy.character.getJointName(joint)
                if jointName in rd.NodePhy:
                    foundJoint = True
                    break
                else:
                    joint = cCopy.character.getJointParent(joint)
            if foundJoint:
                #print("Applying force", forceVector, "to joint", jointName, "at pos", forcePosition)
                rd.setEnabled(True, jointName, forceVector, forcePosition)
            else:
                rd.setEnabled(True, "bip_pelvis", forceVector, forcePosition)
        Ragdolls.append((cCopy, rd))

        return (cCopy, rd)

        #self.resetSequence(-1)

    def setupHitBoxes(self):
        if self.model not in ModelDefs:
            return

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
        body.setOverallHidden(True)
        hbox = HitBox(group, body, joint)
        # Add a link to ourself so traces know who they hit.
        body.setPythonTag("hitbox", (self, hbox))
        body.setPythonTag("entity", self)
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
        # Assume we're visible if render or viewmodel render is the top of our
        # hierarchy.  FIXME: better solution for this
        top = self.getTop()
        visible = (top in [render, base.vmRender]) and not self.isHidden()
        if not visible:
            return

        queue = AnimEventQueue()
        self.character.getEvents(queue, AnimEventType.Client)

        if not queue.hasEvent():
            return

        pos = self.getPos(render)
        hpr = self.getHpr(render)

        while queue.hasEvent():
            info = queue.popEvent()
            channel = self.character.getChannel(info.channel)
            event = channel.getEvent(info.event)
            self.fireEvent(pos, hpr, event.getEvent(), event.getOptions())

    def fireEvent(self, pos, angles, event, options):
        if event == AnimEvent.Client_Play_Sound:
            soundName = options
            sound = createSoundByName(soundName)
            if not sound:
                return
            info = Sounds[soundName]
            if info.channel in self.soundsByChannel:
                currSound = self.soundsByChannel[info.channel]
                if currSound:
                    currSound.stop()
            self.soundsByChannel[info.channel] = sound
            sound.set3dAttributes(pos[0], pos[1], pos[2], 0, 0, 0)
            sound.play()

        elif event == AnimEvent.Client_Bodygroup_Set_Value:
            name, value = options.split()
            self.setBodygroupValue(name, int(value))

    def getChannelForActivity(self, activity, layer=0):
        if hasattr(base, 'net') and hasattr(base.net, 'prediction') and base.net.prediction.inPrediction:
            return Actor.getChannelForActivity(
                self,
                activity, "modelRoot",
                base.net.predictionRandomSeed, layer)
        else:
            return Actor.getChannelForActivity(self, activity, layer=layer)

    def startChannel(self, chan = None, act = None, layer = 0,
                     blendIn = 0.0, blendOut = 0.0, autoKill = False,
                     restart = True):
        if chan is None and act is None:
            return

        if act is not None:
            chan = self.getChannelForActivity(act, layer=layer)

        if chan < 0:
            # Invalid channel, stop the layer we wanted to play it on.
            self.stop(layer=layer)
            return

        char = self.getPartBundle()
        if char.getNumAnimLayers() > layer:
            animLayer = char.getAnimLayer(layer)
            if animLayer._sequence == chan and not restart:
                # The layer is already playing this channel and we don't want
                # to restart, so do nothing.
                return

        channel = char.getChannel(chan)
        if channel.hasFlags(channel.FLooping):
            self.loop(channel=chan, layer=layer, blendIn=blendIn)
        else:
            self.play(channel=chan, layer=layer, blendIn=blendIn,
                      blendOut=blendOut, autoKill=autoKill)

        if act is not None:
            # Store the activity we got the channel from on the layer.
            animLayer = char.getAnimLayer(layer)
            animLayer._activity = act

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

    def getCharacter(self):
        return self.character

    def setJointMergeCharacter(self, char):
        if not self.character:
            return
        self.character.setJointMergeCharacter(char)

    def getJointMergeCharacter(self):
        if not self.character:
            return None
        return self.character.getJointMergeCharacter()

    def setJointMerge(self, jointName, enable = True):
        if not self.character:
            return
        jointIdx = self.character.findJoint(jointName)
        if jointIdx == -1:
            return
        self.character.setJointMerge(jointIdx, enable)

    def getJointMerge(self, jointName):
        if not self.character:
            return
        jointIdx = self.character.findJoint(jointName)
        if jointIdx == -1:
            return
        self.character.getJointMerge(jointIdx)

    def clearModel(self):
        self.removePart("modelRoot")
        self.characterNp = None
        self.character = None
        self.modelNp = None
        self.bodygroups = {}
        self.model = ""
        # Just dropping the references to the hit boxes is good enough to free
        # them from both the physics world and memory.
        for hbox in self.hitBoxes:
            hbox.body.removeFromScene(base.physicsWorld)
        self.hitBoxes = []
        self.lastHitBoxSyncTime = 0.0

    def onModelChanged(self):
        pass

    def loadBodygroups(self):
        data = self.getPartModel().node().getCustomData()
        if not data:
            return
        if not data.hasAttribute("bodygroups"):
            return
        bgs = data.getAttributeValue("bodygroups").getList()
        for i in range(len(bgs)):
            bgdata = bgs.get(i).getElement()
            name = bgdata.getAttributeValue("name").getString()
            self.bodygroups[name] = []
            nodes = bgdata.getAttributeValue("nodes").getList()
            for j in range(len(nodes)):
                pattern = nodes.get(j).getString()
                if pattern == "blank":
                    self.bodygroups[name].append(NodePathCollection())
                else:
                    self.bodygroups[name].append(
                        self.findAllMatches("**/" + pattern))

        for name in self.bodygroups.keys():
            self.setBodygroupValue(name, 0)

    def makeModelCollisionShape(self):
        cinfo = self.getPartModel().node().getCollisionInfo()
        if not cinfo:
            return None

        mdata = PhysConvexMeshData(cinfo.getMeshData())
        if not mdata.generateMesh():
            return None
        mesh = PhysConvexMesh(mdata)
        mat = PhysMaterial(0.5, 0.5, 0.5)
        shape = PhysShape(mesh, mat)
        return shape

    def loadModel(self, model):
        if self.model == model:
            return

        self.clearModel()

        self.model = model

        if len(model) == 0:
            return

        Actor.loadModel(self, model, keepModel=True)

        self.modelNp = self.getPartModel()

        modelNode = self.modelNp.node()

        cdata = modelNode.getCustomData()
        if cdata:
            if cdata.hasAttribute("omni") and cdata.getAttributeValue("omni").getBool():
                modelNode.setBounds(OmniBoundingVolume())

        # We don't need to consider culling past the root of the model.
        modelNode.setFinal(True)

        self.characterNp = self.getPart()
        self.character = self.getPartBundle()

        self.setupHitBoxes()

        if hasattr(base, 'camera'):
            for eyeNp in self.findAllMatches("**/+EyeballNode"):
                eyeNp.node().setViewTarget(base.camera, Point3())

        self.loadBodygroups()

        self.updateModelSkin()

        self.onModelChanged()

    def setSequence(self, seq):
        if not self.character:
            return
        layer = self.character.getAnimLayer(0)
        layer._sequence = seq
        layer._order = 0
        layer._weight = 1.0
        layer._flags |= layer.FActive

    def getCurrSequence(self):
        return self.getCurrentChannel()

    def setCycle(self, cycle):
        if not self.character:
            return
        layer = self.character.getAnimLayer(0)
        layer._cycle = cycle

    def getCycle(self):
        if not self.character:
            return 0.0
        layer = self.character.getAnimLayer(0)
        return float(layer._cycle)

    def setNewSequenceParity(self, parity):
        if not self.character:
            return
        layer = self.character.getAnimLayer(0)
        layer._sequence_parity = parity

    def getNewSequenceParity(self):
        if not self.character:
            return 0
        layer = self.character.getAnimLayer(0)
        return int(layer._sequence_parity)

    def getPrevSequenceParity(self):
        if not self.character:
            return 0
        return int(self.character.getAnimLayer(0)._prev_sequence_parity)


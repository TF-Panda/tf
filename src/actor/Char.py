
from panda3d.core import *
from panda3d.pphysics import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.actor.Actor import Actor
from direct.directbase import DirectRender

from .Activity import Activity
from .AnimEvents import AnimEvent, AnimEventType
from .HitBox import HitBox
from tf.tfbase.Sounds import Sounds, createSoundByName, Channel
from tf.tfbase.TFGlobals import CollisionGroup, Contents
from tf.tfbase.SurfaceProperties import SurfaceProperties

from tf.actor.Ragdoll import Ragdoll

class Char(Actor):
    notify = directNotify.newCategory("Char")

    def __init__(self):
        Actor.__init__(self, flattenable=1, setFinal=1)

        self.character = None
        self.characterNp = None
        self.modelNp = None
        self.hullNp = None
        self.hitBoxes = []
        #self.soundsByChannel = {}
        self.bodygroups = {}
        # Filename of the model.
        self.model = ""

        self.resetEventsParity = 0
        self.prevResetEventsParity = 0
        self.prevEventCycle = -0.01
        self.lastEventSequence = -1

        self.lastHitBoxSyncTime = 0.0

        self.skin = 0

        if base.showingBounds:
            self.showBounds()
        self.accept('show-bounds', self.showBounds)
        self.accept('hide-bounds', self.hideBounds)

    def setBodygroupValue(self, group, value):
        bg = self.bodygroups.get(group)
        if not bg:
            return

        for i in range(len(bg)):
            body = bg[i]
            if i == value:
                body.show()
            else:
                body.hide()

    def getBodygroupNodes(self, group, value):
        """
        Returns the set of NodePaths that are turned on by the given bodygroup
        value.
        """

        bg = self.bodygroups.get(group)
        if not bg:
            return NodePathCollection()

        return bg[value]

    def setSkin(self, skin):
        if skin != self.skin:
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
        # Hide ourselves.
        self.hide()

        collInfo = self.modelNp.node().getCollisionInfo()
        if not collInfo or (collInfo.getNumParts() < 2):
            # No ragdoll for this model.
            return None

        forceVector = Vec3(forceVector[0], forceVector[1], forceVector[2])
        forcePosition = Point3(forcePosition[0], forcePosition[1], forcePosition[2])

        # Make sure the joints reflect the current animation in case we were
        # hidden or off-screen.
        Actor.update(self)

        cCopy = Char()
        cCopy.setSkin(self.skin)
        cCopy.loadModel(self.model, loadHitBoxes=False)
        #cCopy.node().setBounds(OmniBoundingVolume())
        cCopy.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
        # Copy the current joint positions of our character to the ragdoll
        # version.
        character = self.getPartBundle("modelRoot")
        cCharacter = cCopy.getPartBundle("modelRoot")
        for i in range(character.getNumJoints()):
            cCharacter.setJointForcedValue(i, character.getJointValue(i))
        cCopy.reparentTo(base.dynRender)
        cCopy.setTransform(self.getNetTransform())

        # Create the ragdoll using the model's collision info.
        rd = Ragdoll(cCopy, collInfo)
        rd.setup()
        if forceJoint == -1:
            rd.setEnabled(True, None, forceVector, forcePosition)
        else:
            # Find the closest joint to apply the force to.
            joint = forceJoint
            jointName = ""
            foundJoint = False
            while not foundJoint and joint != -1:
                jointName = cCopy.character.getJointName(joint)
                if rd.getJointByName(jointName) is not None:
                    foundJoint = True
                    break
                else:
                    joint = cCopy.character.getJointParent(joint)

            if foundJoint:
                print("Applying force", forceVector, "to joint", jointName, "at pos", forcePosition)
                rd.setEnabled(True, jointName, forceVector, forcePosition)
            else:
                rd.setEnabled(True, None, forceVector, forcePosition)
        #Ragdolls.append((cCopy, rd))

        return (cCopy, rd)

        #self.resetSequence(-1)

    def setupHitBoxes(self):
        """
        Creates hit-boxes for the model using the info from the model's custom
        data structure.
        """
        data = self.modelNp.node().getCustomData()
        if not data or not data.hasAttribute("hit_boxes"):
            return
        hitBoxes = data.getAttributeValue("hit_boxes").getList()
        for i in range(len(hitBoxes)):
            hitBox = hitBoxes.get(i).getElement()
            mins = hitBox.getAttributeValue("mins").getList()
            maxs = hitBox.getAttributeValue("maxs").getList()
            self.addHitBox(hitBox.getAttributeValue("group").getInt(),
                           hitBox.getAttributeValue("joint").getString(),
                           (mins.get(0).getFloat(), mins.get(1).getFloat(), mins.get(2).getFloat()),
                           (maxs.get(0).getFloat(), maxs.get(1).getFloat(), maxs.get(2).getFloat()))

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
        mat = SurfaceProperties[self.getModelSurfaceProp()].getPhysMaterial()
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

        now = globalClock.frame_time
        if now == self.lastHitBoxSyncTime:
            # We're already synchronized with the current point in time.
            return

        self.lastHitBoxSyncTime = now

        for hbox in self.hitBoxes:
            joint = hbox.joint
            body = hbox.body
            body.setTransform(TransformState.makeMat(self.character.getJointNetTransform(joint)))

    def doAnimationEvents(self):
        if not self.character:
            return

        # Assume we're visible if render or viewmodel render is the top of our
        # hierarchy.  FIXME: better solution for this
        top = self.getTop()
        visible = top not in (base.hidden, NodePath()) and not self.isHidden()
        if not visible or (base.cr.prediction.inPrediction and not base.cr.prediction.firstTimePredicted):
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

    def doAnimEventSound(self, soundName):
        pass

    def fireEvent(self, pos, angles, event, options):
        if event == AnimEvent.Client_Play_Sound:
            self.doAnimEventSound(options)

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
        if not self.character:
            return None
        return self.character.addPoseParameter(name, minVal, maxVal, looping)

    def findPoseParameter(self, name):
        if not self.character:
            return None
        return self.character.findPoseParameter(name)

    def getPoseParameter(self, name):
        if not self.character:
            return None

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

    def delete(self, removeNode=True):
        """
        Deletes the model and releases all references.  Call this when you are
        getting rid of the Char for good.  Also see clearModel() if you just
        want to swap out models.

        Set removeNode to False if a derived class needs to perform additional
        cleanup before node removal that relies on the node still existing.
        """

        # Release references.
        self.characterNp = None
        self.character = None
        self.modelNp = None
        self.bodygroups = None
        self.model = None

        self.ignoreAll()

        # Remove hitboxes from the physics scene and release references.
        for hbox in self.hitBoxes:
            hbox.body.removeFromScene(base.physicsWorld)
            hbox.body = None
        self.hitBoxes = None

        # Stop all anim event sounds and release references.
        #for snd in list(self.soundsByChannel.values()):
        #    snd.stop()
        #self.soundsByChannel = None

        # Perform actor cleanup.
        Actor.delete(self, removeNode=removeNode)

    def clearModel(self):
        """
        Unloads the current model, in expectation for another
        model to be loaded in its place.  Use delete() to get rid
        of the Char for good.
        """
        self.removePart()
        self.characterNp = None
        self.character = None
        self.modelNp = None
        self.bodygroups = {}
        self.model = ""
        # Just dropping the references to the hit boxes is good enough to free
        # them from both the physics world and memory.
        for hbox in self.hitBoxes:
            hbox.body.removeFromScene(base.physicsWorld)
            hbox.body = None
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

    def getModelSurfaceProp(self):
        surfaceProp = "default"
        data = self.getPartModel().node().getCustomData()
        if data:
            if data.hasAttribute("surfaceprop"):
                surfaceProp = data.getAttributeValue("surfaceprop").getString().lower()
        return surfaceProp

    def makeModelCollisionShape(self):
        cinfo = self.getPartModel().node().getCollisionInfo()
        if not cinfo:
            return None
        part = cinfo.getPart(0)

        surfaceProp = self.getModelSurfaceProp()

        if part.concave:
            mdata = PhysTriangleMeshData(part.mesh_data)
        else:
            mdata = PhysConvexMeshData(part.mesh_data)
        if not mdata.generateMesh():
            return None
        if part.concave:
            mesh = PhysTriangleMesh(mdata)
        else:
            mesh = PhysConvexMesh(mdata)
        mat = SurfaceProperties[surfaceProp].getPhysMaterial()
        shape = PhysShape(mesh, mat)
        return (shape, mesh)

    def loadModel(self, model, loadHitBoxes=True):
        if self.model == model:
            return

        if self.modelNp is not None:
            # Clear existing model.
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
            if cdata.hasAttribute("bbox"):
                # Model specifies a user bounding volume.
                # Note that this doesn't override the bounds of the geometry
                # of the model, it just unions with it.
                mins = Point3()
                maxs = Point3()
                bbox = cdata.getAttributeValue("bbox").getElement()
                bbox.getAttributeValue("mins").toVec3(mins)
                bbox.getAttributeValue("maxs").toVec3(maxs)
                modelNode.setBounds(BoundingBox(mins, maxs))

        # We don't need to consider culling past the root of the model.
        modelNode.setFinal(True)

        self.characterNp = self.getPart()
        self.character = self.getPartBundle()

        if loadHitBoxes:
            self.setupHitBoxes()

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
        if self.character.getAutoAdvanceFlag():
            # If we're auto advancing (client-side animation),
            # the cycle is computed from the unclamped cycle.
            layer._unclamped_cycle = cycle
        else:
            # Without auto advance, we control the cycle directly.
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


"""Actor module: contains the Actor class."""

from panda3d.core import *
from panda3d.pphysics import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.directbase import DirectRender

from .Model import Model
from tf.tfbase.SurfaceProperties import SurfaceProperties
from tf.tfbase.TFGlobals import Contents
from .HitBox import HitBox
from .Ragdoll import Ragdoll

from .Activity import Activity
from .AnimEvents import AnimEventType, AnimEvent

class Actor(Model):
    """
    High-level interface for animated characters.  It can be used with static
    models too, but the animation-related methods won't do anything.

    This is a replacment of the original Actor interface, located in
    $DIRECT/src/actor.  The original Actor is very big and clunky, and this
    replacement is intended to be lightweight and better suited for TF2's
    needs.
    """

    notify = directNotify.newCategory("Actor")

    # A global random seed used by all Actors in the world to select a channel
    # from an activity.  This is set during client-side prediction so channel
    # selection from activities is consistent with the server.
    GlobalActivitySeed = 0

    AllCharacters = NodePathCollection()

    def __init__(self):
        Model.__init__(self)

        # Pointer to the Character object from the loaded model.
        self.character = None
        # NodePath to the CharacterNode from the loaded model.
        self.characterNp = None
        self.channelsByName = {}

        # Boxes parented to joints for hit detection.
        # TODO: Use an aggregate.
        self.hitBoxes = []
        self.hitBoxRoot = None
        self.lastHitBoxSyncTime = 0.0

    @staticmethod
    def updateAllAnimations():
        CharacterNode.animateCharacters(Actor.AllCharacters)

    @staticmethod
    def setGlobalActivitySeed(seed):
        """
        Sets the global random seed to use when selecting a channel from an
        activity.
        """
        Actor.GlobalActivitySeed = seed

    @staticmethod
    def clearGlobalActivitySeed():
        """
        Clears the global activity random seed.
        """
        Actor.GlobalActivitySeed = 0

    def isAnimated(self):
        """
        Returns True if the current loaded model is an animated character, or
        False if it's a static model.  This class is designed to allow
        transparent use of animated or static models.  All animation-related
        methods check that the model is animated before doing anything.
        """
        return self.character is not None

    def makeRagdoll(self, forceJoint, forcePosition, forceVector, initialVel = Vec3(0)):

        collInfo = self.modelRootNode.getCollisionInfo()
        if not collInfo or (collInfo.getNumParts() < 2):
            # No ragdoll for this actor.
            return None

        forceVector = Vec3(forceVector[0], forceVector[1], forceVector[2])
        forcePosition = Point3(forcePosition[0], forcePosition[1], forcePosition[2])

        # Make sure the joints reflect the current animation in case we were
        # hidden or off-screen.
        self.updateAnimation()

        ragdollActor = Actor()
        ragdollActor.setSkin(self.skin)
        ragdollActor.loadModel(self.model, hitboxes=False)
        ragdollActor.modelNp.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
        # Copy the current joint positions of our character to the ragdoll
        # version.
        for i in range(self.character.getNumJoints()):
            ragdollActor.character.setJointForcedValue(i, self.character.getJointValue(i))
        ragdollActor.modelNp.reparentTo(base.dynRender)
        ragdollActor.modelNp.setTransform(self.modelNp.getNetTransform())

        # Create the ragdoll using the model's collision info.
        rd = Ragdoll(ragdollActor.characterNp, collInfo)
        rd.setup()
        if forceJoint == -1:
            rd.setEnabled(True, None, forceVector, forcePosition, initialVel)
        else:
            # Find the closest joint to apply the force to.
            joint = forceJoint
            jointName = ""
            foundJoint = False
            while not foundJoint and joint != -1:
                jointName = ragdollActor.character.getJointName(joint)
                if rd.getJointByName(jointName):
                    foundJoint = True
                    break
                else:
                    joint = ragdollActor.character.getJointParent(joint)

            if foundJoint:
                rd.setEnabled(True, jointName, forceVector, forcePosition, initialVel)
            else:
                rd.setEnabled(True, None, forceVector, forcePosition, initialVel)

        return (ragdollActor, rd)

    def setChannelTransition(self, flag):
        if self.character:
            self.character.setChannelTransitionFlag(flag)

    def setAutoAdvance(self, flag):
        if self.character:
            self.character.setAutoAdvanceFlag(flag)

    def setFrameBlend(self, flag):
        if self.character:
            self.character.setFrameBlendFlag(flag)

    def getChannelForActivity(self, activity, layer=0):
        if not self.character:
            return -1

        return self.character.getChannelForActivity(activity, self.getCurrentAnim(layer),
            Actor.GlobalActivitySeed)

    def setAnim(self, anim = None, activity = None, playRate = 1.0, layer = 0,
                blendIn = 0.0, blendOut = 0.0, autoKill = False,
                loop = None, restart = False, fromFrame = None,
                toFrame = None):
        """
        Starts an animation channel playing on the actor.

        If `loop` is not specified, loops the animation based on the
        if the channel itself has the looping flag set.
        """

        if not self.character:
            return

        if anim is None and activity is None:
            return

        if activity is not None:
            # Randomly select between all animations associated with the
            # activity.
            anim = self.character.getChannelForActivity(activity, self.getCurrentAnim(layer),
                                                        Actor.GlobalActivitySeed)
        elif isinstance(anim, str):
            # Animation specified by string name.  Find the channel index
            # associated with that name.
            animName = anim
            anim = self.channelsByName.get(animName, -1)
            if anim < 0:
                self.notify.warning("No animation channel named %s on character %s" % (animName, self.character.getName()))
                return
        # Otherwise, an explicit channel index was specified.

        if anim < 0 or anim >= self.character.getNumChannels():
            self.notify.warning("Invalid animation channel %i for character %s" % (anim, self.character.getName()))
            return

        channel = self.character.getChannel(anim)

        if fromFrame is None:
            fromFrame = 0
        if toFrame is None:
            toFrame = channel.getNumFrames() - 1

        if loop is not None:
            doLoop = loop
        else:
            doLoop = channel.hasFlags(channel.FLooping)

        if doLoop:
            self.character.loop(anim, restart, fromFrame, toFrame, layer,
                                playRate, blendIn)
        else:
            self.character.play(anim, fromFrame, toFrame, layer, playRate,
                                autoKill, blendIn, blendOut)

        if activity is not None:
            # Store the activity we got the channel from on the layer.
            alayer = self.character.getAnimLayer(layer)
            alayer._activity = activity

        self.considerProcessAnimationEvents()

    def stopAnim(self, layer = None, kill = False):
        """
        Stops whatever animation channel is playing on the indicated layer,
        or all layers if `layer` is None.  If kill is True, the layer will be
        faded out before actually stopping the animation.
        """

        if not self.character:
            return

        if layer is None or layer < 0:
            self.character.stop(-1, kill)
        elif layer < self.character.getNumAnimLayers():
            self.character.stop(layer, kill)

        self.considerProcessAnimationEvents()

    def getCurrentAnim(self, layer = 0):
        """
        Returns the index of the animation channel currently playing on the
        indicated layer, or the base layer if unspecified.

        Returns -1 if an invalid layer is specified, no animation is currently
        playing on that layer, or if the actor is not a character.
        """

        if not self.character:
            return -1
        elif not self.character.isValidLayerIndex(layer):
            return -1

        animLayer = self.character.getAnimLayer(layer)
        if not animLayer.isPlaying():
            return -1

        return animLayer._sequence

    def getCurrentAnimChannel(self, layer=0):
        """
        Returns the AnimChannel currently playing on the indicated animation
        layer, or None if no animation is playing (or the model is not animated).
        """

        if not self.character:
            return None
        elif layer < 0 or layer >= self.character.getNumAnimLayers():
            return None

        animLayer = self.character.getAnimLayer(layer)
        if not animLayer.isPlaying():
            return None

        return self.character.getChannel(animLayer._sequence)

    def getCurrentAnimActivity(self, layer = 0):
        """
        Returns the activity associated with the animation channel currently
        playing on the indicated layer, or the base layer if unspecified.

        Returns -1 if an invalid layer is specified, no animation is currently
        playing on that layer, the actor is not a character, or no activity is
        associated with the animation.
        """
        if not self.character:
            return -1
        elif layer < 0 or layer >= self.character.getNumAnimLayers():
            return -1

        animLayer = self.character.getAnimLayer(layer)
        if not animLayer.isPlaying():
            return -1

        return animLayer._activity

    def getCurrentAnimLength(self, layer=0):
        """
        Returns the length in seconds of the animation currently playing on
        the indicated layer, factoring in play rate.
        """
        if not self.character:
            return 0.1

        if not self.character.isValidLayerIndex(layer):
            return 0.1

        alayer = self.character.getAnimLayer(layer)
        if not self.character.isValidChannelIndex(alayer._sequence):
            return 0.1

        chan = self.character.getChannel(alayer._sequence)
        playRate = alayer._play_rate

        return chan.getLength(self.character) / playRate

    def getAnimActivity(self, anim, index=0):
        """
        Returns the activity associated with the indicated animation channel,
        by name or index.
        """
        if not self.character:
            return -1
        if isinstance(anim, str):
            anim = self.channelsByName.get(anim, -1)

        if not self.character.isValidChannelIndex(anim):
            return -1

        chan = self.character.getChannel(anim)
        if chan.getNumActivities() == 0:
            return -1
        return chan.getActivity(index)

    def getAnimLength(self, anim):
        if not self.character:
            return 0.01

        if isinstance(anim, str):
            anim = self.channelsByName.get(anim, -1)

        if not self.character.isValidChannelIndex(anim):
            return 0.01

        chan = self.character.getChannel(anim)
        return chan.getLength(self.character)

    def isAnimFinished(self, layer = 0):
        """
        Returns True if the animation channel playing on the indicated layer
        is finished or no animation is playing on the layer.

        Note that a looping or ping-ponging animation channel is never
        finished.
        """
        return self.getCurrentAnim(layer) == -1

    def isAnimPlaying(self, layer = 0):
        """
        Returns True if an animation is currently playing on the indicated
        layer.
        """

        if not self.character:
            return False
        elif not self.character.isValidLayerIndex(layer):
            return False

        animLayer = self.character.getAnimLayer(layer)
        return animLayer.isPlaying()

    def setCycle(self, cycle, layer=0):
        """
        Overrides the cycle of whatever animation is currently playing
        on the indicated layer.
        """
        if not self.character:
            return

        if not self.character.isValidLayerIndex(layer):
            return

        animLayer = self.character.getAnimLayer(layer)
        if self.character.getAutoAdvanceFlag():
            # If we're auto advancing (client-side animation),
            # the cycle is computed from the unclamped cycle.
            animLayer._unclamped_cycle = cycle
        else:
            # Without auto advance, we control the cycle directly.
            animLayer._cycle = cycle

    def getCycle(self, layer=0):
        if not self.character:
            return 0.0

        if not self.character.isValidLayerIndex(layer):
            return 0.0

        animLayer = self.character.getAnimLayer(layer)
        return animLayer._cycle

    def setPlayRate(self, rate, layer = 0):
        """
        Updates the play rate of the indicated animation layer.
        """
        if not self.character:
            return

        if layer < 0 or layer >= self.character.getNumAnimLayers():
            return

        self.character.getAnimLayer(layer)._play_rate = rate

    def getPlayRate(self, layer = 0):
        """
        Returns the play rate of the indicated animation layer.
        """
        if not self.character:
            return 1.0

        if layer < 0 or layer >= self.character.getNumAnimLayers():
            return 1.0

        return self.character.getAnimLayer(layer)._play_rate

    def getPoseParameter(self, nameOrIndex):
        """
        Returns the pose parameter with the indicated name or index, or None
        if the pose parameter is not found.
        """
        if not self.character:
            return None

        if isinstance(nameOrIndex, str):
            idx = self.character.findPoseParameter(nameOrIndex)
            if idx == -1:
                return None
            return self.character.getPoseParameter(idx)

        return self.character.getPoseParameter(nameOrIndex)

    def setJointMergeCharacter(self, char):
        """
        Sets the character that joints on this character with joint merge
        enabled should copy their poses from.

        For instance, the weapon's joint merge character is the hands.
        """
        if not self.character:
            return
        self.character.setJointMergeCharacter(char)

    def getAttachment(self, attachment, net = False, update = True):
        """
        Returns the current transform of the indicated attachment as a
        TransformState object.

        If `net` is True, the returned transform will be in world coordinates,
        otherwise it will be relative to the character node (self.characterNp).

        If `update` is True (the default), the character will update its
        animation before querying the attachment transform, if it hasn't
        already been updated this frame.
        """
        if not self.character:
            return TransformState.makeIdentity()

        if isinstance(attachment, str):
            attachmentName = attachment
            attachment = self.character.findAttachment(attachmentName)
            if attachment == -1:
                self.notify.warning("No attachment named %s on character %s" % (attachmentName, self.character.getName()))
                return TransformState.makeIdentity()

        if update:
            self.character.update()

        if net:
            return self.character.getAttachmentNetTransform(attachment)
        return self.character.getAttachmentTransform(attachment)

    def getAttachmentNode(self, attachment):
        """
        Returns the NodePath that is linked to the indicated attachment.

        The returned node is automatically updated with the transform of
        the attachment when the attachment is updated during the animation
        update.  You can parent stuff to this node to have it automatically
        follow the attachment.  You can also ask this node for its transform
        instead of calling `getAttachment()`.
        """

        if not self.character:
            return NodePath()

        if isinstance(attachment, str):
            attachmentName = attachment
            attachment = self.character.findAttachment(attachmentName)
            if attachment == -1:
                self.notify.warning("No attachment named %s on character %s" % (attachmentName, self.character.getName()))
                return NodePath()

        return NodePath.anyPath(self.character.getAttachmentNode(attachment))

    def updateAnimation(self):
        """
        Makes the character update its animation and all joint poses
        immediately instead of waiting until the character is rendered
        later in the frame.

        This is needed on the AI since it doesn't render anything.  The AI
        needs to animate characters for hitbox placement and attachments.
        """
        if not self.character:
            return
        self.character.update()

    def buildAnimTable(self):
        """
        Builds up a mapping of channel names to channel indices on the
        character so the user can refer to channels by name.
        """
        self.channelsByName = {}
        if not self.character:
            return
        for i in range(self.character.getNumChannels()):
            self.channelsByName[self.character.getChannel(i).getName()] = i

    def cleanup(self):
        Model.cleanup(self)
        self.channelsByName = None
        self.lastHitBoxSyncTime = None
        self.hitBoxes = None

    def unloadModel(self):
        """
        Removes the current model from the scene graph and all related data.
        """
        self.stopProcessingAnimationEvents()
        if self.characterNp:
            Actor.AllCharacters.removePath(self.characterNp)
        self.characterNp = None
        self.character = None
        self.channelsByName = {}
        # Remove hitboxes from physics scene and release references.
        for hbox in self.hitBoxes:
            hbox.body.removeFromScene(base.physicsWorld)
            hbox.body = None
        self.hitBoxes = []
        self.hitBoxRoot = None
        Model.unloadModel(self)

    def loadModel(self, filename, hitboxes=True):
        """
        Loads up a model from the indicated model filename.  The existing
        model is unloaded.

        Returns true if the model was loaded successfully, false otherwise.
        """

        if not Model.loadModel(self, filename, callOnChanged=False):
            return False

        if isinstance(self.modelNp.node(), CharacterNode):
            self.characterNp = NodePath(self.modelNp)
        else:
            self.characterNp = self.modelNp.find("**/+CharacterNode")
        if self.characterNp.isEmpty():
            # The model is not an animated character if it does not contain
            # a CharacterNode.
            self.characterNp = None
        else:
            Actor.AllCharacters.addPath(self.characterNp)
            self.character = self.characterNp.node().getCharacter()
            self.buildAnimTable()

            if hitboxes:
                self.setupHitBoxes()

        self.onModelChanged()

        return True

    def setupHitBoxes(self):
        """
        Creates hit-boxes for the model using the info from the model's custom
        data structure.
        """

        data = self.modelData
        if not data or not data.hasAttribute("hit_boxes"):
            return

        hitBoxes = data.getAttributeValue("hit_boxes").getList()

        # Create a single root node for all hitbox nodes to be parented under,
        # and hide it from rendering.  This way the Cull traversal only has
        # to consider the root node, and not all the individual hitbox nodes.
        if len(hitBoxes) > 0:
            self.hitBoxRoot = self.characterNp.attachNewNode("hitBoxRoot")
            self.hitBoxRoot.node().setOverallHidden(True)

        assert self.characterNp

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
        body.setPythonTag("object", self)
        self.hitBoxes.append(hbox)
        assert self.hitBoxRoot
        self.hitBoxRoot.attachNewNode(body)

    def syncHitBoxes(self):
        """
        Synchronizes the physics bodies of character's hit boxes with the
        current world-space transform of the associated joints.
        """

        if not self.hitBoxes:
            return

        #now = globalClock.frame_time
        #if now == self.lastHitBoxSyncTime:
            # We're already synchronized with the current point in time.
        #    return

        #self.lastHitBoxSyncTime = now

        for hbox in self.hitBoxes:
            hbox.body.setTransform(
                TransformState.makeMat(self.character.getJointNetTransform(hbox.joint)))
            hbox.body.syncTransform()

    def invalidateHitBoxes(self):
        self.lastHitBoxSyncTime = 0.0

    def needsToProcessAnimationEvents(self):
        if not self.character:
            return False

        # If any channel playing on any layer has events, we need to
        # process animation events.
        for i in range(self.character.getNumAnimLayers()):
            alayer = self.character.getAnimLayer(i)
            if alayer.isPlaying() and alayer._sequence != -1:
                chan = self.character.getChannel(alayer._sequence)
                if chan.getNumEvents() > 0:
                    return True

        return False

    def considerProcessAnimationEvents(self):
        if self.needsToProcessAnimationEvents():
            self.startProcessingAnimationEvents()
        else:
            self.stopProcessingAnimationEvents()

    def startProcessingAnimationEvents(self):
        pass

    def stopProcessingAnimationEvents(self):
        pass

    def doAnimationEvents(self, eventType=AnimEventType.Client):
        if not self.character:
            return

        assert self.modelNp
        if (base.cr.prediction.inPrediction and not base.cr.prediction.firstTimePredicted) or \
           (self.modelNp.getTop() in (base.hidden, NodePath()) or self.modelNp.isHidden()):
            return

        queue = AnimEventQueue()
        self.character.getEvents(queue, eventType)

        if not queue.hasEvent():
            return

        while queue.hasEvent():
            info = queue.popEvent()
            channel = self.character.getChannel(info.channel)
            event = channel.getEvent(info.event)
            self.fireAnimEvent(event.getEvent(), event.getOptions())

    def fireAnimEvent(self, event, options):
        if event == AnimEvent.Client_Play_Sound:
            self.doAnimEventSound(options)

        elif event == AnimEvent.Client_Bodygroup_Set_Value:
            name, value = options.split()
            self.setBodygroupValue(name, int(value))

    def doAnimEventSound(self, soundName):
        pass

    def controlJoint(self, node, jointName):
        """
        Gives the indicated node control of the indicated joint.

        If node is None, creates a new node with the same name
        as the joint that can be used to control the joint.

        Returns the node.
        """

        if not node:
            node = NodePath(ModelNode(jointName))

        if not self.character:
            self.notify.warning("Actor is not animated, can't control joint " + jointName)
            return node

        node.reparentTo(self.characterNp)

        joint = self.character.findJoint(jointName)
        if joint != -1:
            node.setMat(self.character.getJointDefaultValue(joint))
            self.character.setJointControllerNode(joint, node.node())
        else:
            self.notify.warning("controlJoint: joint " + jointName + " not found on character " + self.character.getName())

        return node

    def releaseJoint(self, jointName):
        if not self.character:
            return

        joint = self.character.findJoint(jointName)
        if joint == -1:
            return

        self.character.clearJointControllerNode(joint)

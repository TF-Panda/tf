"""Actor module: contains the Actor class."""

from panda3d.core import *

from direct.directnotify.DirectNotifyGlobal import directNotify

from .Model import Model

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

    def __init__(self):
        Model.__init__(self)

        # Pointer to the Character object from the loaded model.
        self.character = None
        # NodePath to the CharacterNode from the loaded model.
        self.characterNp = None
        self.channelsByName = {}

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

    def getCurrentAnim(self, layer = 0):
        """
        Returns the index of the animation channel currently playing on the
        indicated layer, or the base layer if unspecified.

        Returns -1 if an invalid layer is specified, no animation is currently
        playing on that layer, or if the actor is not a character.
        """

        if not self.character:
            return -1
        elif layer < 0 or layer >= self.character.getNumAnimLayers():
            return -1

        animLayer = self.character.getAnimLayer(layer)
        if not animLayer.isPlaying():
            return -1

        return animLayer._sequence

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

    def isAnimFinished(self, layer = 0):
        """
        Returns True if the animation channel playing on the indicated layer
        is finished or no animation is playing on the layer.

        Note that a looping or ping-ponging animation channel is never
        finished.
        """
        return self.getCurrentAnim(layer) == -1

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

    def unloadModel(self):
        """
        Removes the current model from the scene graph and all related data.
        """
        if self.characterNp:
            self.characterNp.removeNode()
            self.characterNp = None
        self.character = None
        self.channelsByName = {}
        Model.unloadModel(self)

    def loadModel(self, filename):
        """
        Loads up a model from the indicated model filename.  The existing
        model is unloaded.

        Returns true if the model was loaded successfully, false otherwise.
        """

        if not Model.loadModel(self, filename):
            return False

        self.characterNp = self.modelNp.find("**/+CharacterNode")
        if self.characterNp.isEmpty():
            # The model is not an animated character if it does not contain
            # a CharacterNode.
            self.characterNp = None
        else:
            self.character = self.characterNp.node().getCharacter()
            self.buildAnimTable()

        return True


from panda3d.core import *
from panda3d.direct import *

from tf.entity.DistributedEntity import DistributedEntity
from tf.tfbase.TFGlobals import SolidShape

from .Actor import Actor


class DistributedChar(Actor, DistributedEntity):

    AllChars = []

    def __init__(self):
        Actor.__init__(self)
        DistributedEntity.__init__(self)

        # Client-side ragdoll associated with this entity.
        self.ragdoll = None
        self.processingAnimEvents = False

    def fireTracer(self, attachment, endPos, delay=0.0, spread=0.0):
        srcTs = self.getAttachment(attachment, net=True, update=False)
        srcPos = Point3(srcTs.getPos())

        if spread:
            srcPos -= srcTs.getQuat().getForward() * spread

        base.game.doTracer(srcPos, endPos, delay=delay)

    @staticmethod
    def syncAllHitBoxes():
        for char in DistributedChar.AllChars:
            char.syncHitBoxes()

    def RecvProxy_skin(self, skin):
        self.setSkin(skin)

    def RecvProxy_model(self, model):
        if model != self.model:
            self.loadModel(model)

    def startProcessingAnimationEvents(self):
        if not self.processingAnimEvents:
            self.addTask(self.__processAnimationEventsTask, 'processAnimEvents', sim=True, sort=100, appendTask=True)
            self.processingAnimEvents = True

    def stopProcessingAnimationEvents(self):
        if self.processingAnimEvents:
            self.removeTask('processAnimEvents')
            self.processingAnimEvents = False

    def __processAnimationEventsTask(self, task):
        self.doAnimationEvents()
        return task.cont

    def shouldSpatializeAnimEventSounds(self):
        return True

    def doAnimEventSound(self, soundName):
        if self.shouldSpatializeAnimEventSounds():
            self.emitSoundSpatial(soundName)
        else:
            self.emitSound(soundName)

    def loadModelBBoxIntoHull(self):
        data = self.modelData
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
            assert self.modelRootNode
            cinfo = self.modelRootNode.getCollisionInfo()
            if cinfo:
                cinfo = cinfo.getPart(0)
                assert cinfo
                self.mass = cinfo.mass
                self.damping = cinfo.damping
                self.rotDamping = cinfo.rot_damping

        elif self.solidShape == SolidShape.Box:
            self.loadModelBBoxIntoHull()

        DistributedEntity.initializeCollisions(self)

    def makeModelCollisionShape(self):
        return Actor.makeModelCollisionShape(self)

    def onModelChanged(self):
        self.initializeCollisions()
        if self.modelNp:
            # Parent model to entity.
            self.modelNp.reparentTo(self)
        Actor.onModelChanged(self)

    def becomeRagdoll(self, forceJoint, forcePosition, forceVector, initialVel):
        if self.ragdoll:
            # Remove existing ragdoll.
            self.ragdoll[0].cleanup()
            self.ragdoll[1].destroy()
            self.ragdoll = None

        self.ragdoll = self.makeRagdoll(forceJoint, forcePosition, forceVector, initialVel)

        return self.ragdoll

    def setModel(self, filename):
        self.loadModel(filename)

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        DistributedChar.AllChars.append(self)

    def disable(self):
        if self.ragdoll:
            self.ragdoll[0].cleanup()
            self.ragdoll[1].destroy()
        self.ragdoll = None
        DistributedChar.AllChars.remove(self)
        DistributedEntity.disable(self)

    def delete(self):
        self.cleanup()
        DistributedEntity.delete(self)

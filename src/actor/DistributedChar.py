
from tf.entity.DistributedEntity import DistributedEntity
from .Char import Char

from tf.tfbase.TFGlobals import SolidShape

from panda3d.core import *
from panda3d.direct import *

class DistributedChar(Char, DistributedEntity):

    def __init__(self):
        Char.__init__(self)
        DistributedEntity.__init__(self)

        # Client-side ragdoll associated with this entity.
        self.ragdoll = None

    def RecvProxy_skin(self, skin):
        self.setSkin(skin)

    def RecvProxy_model(self, model):
        self.loadModel(model)

    def shouldSpatializeAnimEventSounds(self):
        return True

    def doAnimEventSound(self, soundName):
        if self.shouldSpatializeAnimEventSounds():
            self.emitSoundSpatial(soundName)
        else:
            self.emitSound(soundName)

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

    def postInterpolate(self):
        DistributedEntity.postInterpolate(self)
        if globalClock.dt != 0.0:
            self.doAnimationEvents()

    def setModel(self, filename):
        self.loadModel(filename)

    def disable(self):
        if self.ragdoll:
            self.ragdoll[1].destroy()
            self.ragdoll[0].delete()
        self.ragdoll = None
        DistributedEntity.disable(self)

    def delete(self):
        Char.delete(self, removeNode=False)
        DistributedEntity.delete(self)

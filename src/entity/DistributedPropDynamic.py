"""DistributedPropDynamic module: contains the DistributedPropDynamic class."""

if not IS_CLIENT:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI
else:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar

from panda3d.core import Filename, VirtualFileSystem, getModelPath, BoundingSphere

from tf.tfbase.TFGlobals import SolidShape, SolidFlag

class DistributedPropDynamic(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        # Animation index.
        self.animation = 0
        self.solid = False

        self.solidShape = SolidShape.Model
        self.solidFlags = SolidFlag.Tangible

    if not IS_CLIENT:

        def setAnimation(self, animName):
            self.setAnim(animName, layer=0)
            self.animation = self.getCurrentAnim()

        def initFromLevel(self, ent, props):
            BaseClass.initFromLevel(self, ent, props)

            if props.hasAttribute("skin"):
                self.skin = props.getAttributeValue("skin").getInt()

            if props.hasAttribute("model"):
                fname = Filename.fromOsSpecific(props.getAttributeValue("model").getString().replace(".mdl", ".bam"))
                vfs = VirtualFileSystem.getGlobalPtr()
                if vfs.resolveFilename(fname, getModelPath().value):
                    self.setModel(fname.getFullpath())

            if props.hasAttribute("solid"):
                self.solid = props.getAttributeValue("solid").getBool()

                if self.solid and self.modelNp:
                    self.initializeCollisions()
    else:

        def RecvProxy_model(self, mdl):
            if not mdl:
                self.node().setBounds(BoundingSphere((0, 0, 0), 16.0))
            else:
                self.node().clearBounds()
            BaseClass.RecvProxy_model(self, mdl)

        def RecvProxy_animation(self, anim):
            if anim != self.animation:
                self.setAnim(anim, layer=0)
                self.animation = anim

        def announceGenerate(self):
            BaseClass.announceGenerate(self)
            if self.solid and self.modelNp:
                self.initializeCollisions()

if not IS_CLIENT:
    DistributedPropDynamicAI = DistributedPropDynamic
    DistributedPropDynamicAI.__name__ = 'DistributedPropDynamicAI'

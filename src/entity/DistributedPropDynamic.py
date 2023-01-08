"""DistributedPropDynamic module: contains the DistributedPropDynamic class."""

if not IS_CLIENT:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI
else:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar

from tf.actor.Actor import Actor

from panda3d.core import Filename, VirtualFileSystem, getModelPath, BoundingSphere

from tf.tfbase.TFGlobals import SolidShape, SolidFlag

class DistributedPropDynamic(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        # Animation index.
        self.animation = -1
        self.solid = False
        self.enabled = True

        self.solidShape = SolidShape.Empty
        self.solidFlags = SolidFlag.Tangible

    def setEnabled(self, flag):
        if flag:
            if self.modelNp:
                self.modelNp.unstash()
            if self.solid:
                self.initializeCollisions()
        else:
            self.destroyCollisions()
            if self.modelNp:
                self.modelNp.stash()
        self.enabled = flag

    def onModelChanged(self):
        if self.modelNp:
            self.modelNp.reparentTo(self)
            if not self.enabled:
                self.modelNp.stash()
        if self.enabled and self.solid:
            self.initializeCollisions()
        else:
            self.destroyCollisions()
        Actor.onModelChanged(self)

    if not IS_CLIENT:

        def input_Skin(self, caller, skin):
            self.skin = int(skin)

        def input_TurnOn(self, caller):
            self.setEnabled(True)

        def input_Enable(self, caller):
            self.setEnabled(True)

        def input_TurnOff(self, caller):
            self.setEnabled(False)

        def input_Disable(self, caller):
            self.setEnabled(False)

        def setAnimation(self, animName):
            self.setAnim(animName, layer=0)
            self.animation = self.getCurrentAnim()

        def initFromLevel(self, ent, props):
            BaseClass.initFromLevel(self, ent, props)

            if props.hasAttribute("skin"):
                self.skin = props.getAttributeValue("skin").getInt()

            if props.hasAttribute("solid"):
                self.solid = props.getAttributeValue("solid").getBool()
                if self.solid:
                    self.solidShape = SolidShape.Model

            if props.hasAttribute("StartDisabled"):
                self.enabled = not props.getAttributeValue("StartDisabled").getBool()

            if props.hasAttribute("model"):
                fname = Filename.fromOsSpecific(props.getAttributeValue("model").getString().replace(".mdl", ".bam"))
                vfs = VirtualFileSystem.getGlobalPtr()
                resolved = Filename(fname)
                if vfs.resolveFilename(resolved, getModelPath().value):
                    self.setModel(fname.getFullpath())

                    if props.hasAttribute("DefaultAnim"):
                        animName = props.getAttributeValue("DefaultAnim").getString()
                        self.setAnimation(animName)
                    else:
                        self.setAnimation(0)
                else:
                    print("prop_dynamic model", fname, "does not exist, port it!")

    else:

        def RecvProxy_enabled(self, flag):
            self.setEnabled(flag)

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
                self.solidShape = SolidShape.Model

            self.setEnabled(self.enabled)

if not IS_CLIENT:
    DistributedPropDynamicAI = DistributedPropDynamic
    DistributedPropDynamicAI.__name__ = 'DistributedPropDynamicAI'

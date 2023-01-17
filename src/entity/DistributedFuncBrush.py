"""DistributedFuncBrush module: contains the DistributedFuncBrush class."""

from .DistributedSolidEntity import DistributedSolidEntity

from tf.tfbase.TFGlobals import SolidFlag, SolidShape

class DistributedFuncBrush(DistributedSolidEntity):

    def __init__(self):
        DistributedSolidEntity.__init__(self)
        self.solidFlags = SolidFlag.Tangible
        self.solidShape = SolidShape.Model
        self.physType = self.PTTriangles
        self.isSolid = False

        self.enabled = True

    if not IS_CLIENT:
        def initFromLevel(self, ent, props):
            DistributedSolidEntity.initFromLevel(self, ent, props)

            if props.hasAttribute("Solidity"):
                self.isSolid = props.getAttributeValue("Solidity").getInt() != 1
            elif props.hasAttribute("solid"):
                self.isSolid = props.getAttributeValue("solid").getBool()

            if props.hasAttribute("StartDisabled"):
                self.enabled = not props.getAttributeValue("StartDisabled").getBool()

        def input_Disable(self, caller):
            self.setEnabled(False)

        def input_TurnOff(self, caller):
            self.setEnabled(False)

        def input_Enable(self, caller):
            self.setEnabled(True)

        def input_TurnOn(self, caller):
            self.setEnabled(True)
    else:
        def RecvProxy_enabled(self, flag):
            if flag != self.enabled:
                self.setEnabled(flag)

    def setEnabled(self, flag):
        self.enabled = flag
        if self.enabled:
            if self.isSolid:
                self.initializeCollisions()
            if self.modelNp:
                self.modelNp.unstash()
        else:
            self.destroyCollisions()
            if self.modelNp:
                self.modelNp.stash()

    def announceGenerate(self):
        DistributedSolidEntity.announceGenerate(self)
        self.setEnabled(self.enabled)

if not IS_CLIENT:
    DistributedFuncBrushAI = DistributedFuncBrush
    DistributedFuncBrushAI.__name__ = 'DistributedFuncBrushAI'

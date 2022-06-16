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

    if not IS_CLIENT:
        def initFromLevel(self, ent, props):
            DistributedSolidEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("Solidity"):
                self.isSolid = props.getAttributeValue("Solidity").getInt() != 1
            elif props.hasAttribute("solid"):
                self.isSolid = props.getAttributeValue("solid").getBool()

    def announceGenerate(self):
        DistributedSolidEntity.announceGenerate(self)
        if self.isSolid:
            self.initializeCollisions()

if not IS_CLIENT:
    DistributedFuncBrushAI = DistributedFuncBrush
    DistributedFuncBrushAI.__name__ = 'DistributedFuncBrushAI'

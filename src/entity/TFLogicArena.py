"""TFLogicArena module: contains the TFLogicArena class."""

from .EntityBase import EntityBase

class TFLogicArena(EntityBase):

    def __init__(self):
        EntityBase.__init__(self)
        self.capEnableDelay = 0.0

    def initFromLevel(self, ent, properties):
        EntityBase.initFromLevel(self, ent, properties)
        if properties.hasAttribute("CapEnableDelay"):
            self.capEnableDelay = properties.getAttributeValue("CapEnableDelay").getFloat()

    def generate(self):
        EntityBase.generate(self)
        from tf.distributed.GameModeArena import GameModeArena
        assert isinstance(base.game.gameModeImpl, GameModeArena)
        base.game.gameModeImpl.arenaLogicEnt = self

"""LogicRelay module: contains the LogicRelay class."""

from .EntityBase import EntityBase

class LogicRelay(EntityBase):

    FOnlyOnce = 1

    def __init__(self):
        EntityBase.__init__(self)
        self.spawnflags = 0
        self.fired = False
        self.enabled = True

    def input_Enable(self, caller):
        self.enabled = True

    def input_Disable(self, caller):
        self.enabled = False

    def input_Toggle(self, caller):
        self.enabled = not self.enabled

    def input_Trigger(self, caller):
        if not self.enabled:
            return
        if self.fired and (self.spawnflags & self.FOnlyOnce):
            return
        self.connMgr.fireOutput("OnTrigger")
        self.fired = True

    def announceGenerate(self):
        EntityBase.announceGenerate(self)
        self.connMgr.fireOutput("OnSpawn")

    def initFromLevel(self, ent, properties):
        EntityBase.initFromLevel(self, ent, properties)
        if properties.hasAttribute("spawnflags"):
            self.spawnflags = properties.getAttributeValue("spawnflags").getInt()
        if properties.hasAttribute("StartDisabled"):
            self.enabled = not properties.getAttributeValue("StartDisabled").getBool()

"""InfoPlayerTeamspawn module: contains the InfoPlayerTeamspawn class."""

from panda3d.core import *

from tf.tfbase import TFGlobals

from .EntityBase import EntityBase


class InfoPlayerTeamspawn(EntityBase):

    def __init__(self):
        EntityBase.__init__(self)
        self.team = TFGlobals.TFTeam.NoTeam
        self.spawnPos = Point3()
        self.spawnHpr = Vec3()
        self.enabled = True

        self.controlPointName = ""
        self.controlPoint = None
        self.blueCPRoundName = ""
        self.blueCPRound = None
        self.redCPRoundName = ""
        self.redCPRound = None

    def initFromLevel(self, ent, props):
        EntityBase.initFromLevel(self, ent, props)
        if props.hasAttribute("StartDisabled"):
            self.enabled = not props.getAttributeValue("StartDisabled").getBool()
        if props.hasAttribute("origin"):
            props.getAttributeValue("origin").toVec3(self.spawnPos)
        if props.hasAttribute("angles"):
            props.getAttributeValue("angles").toVec3(self.spawnHpr)
            tmp = self.spawnHpr[0]
            self.spawnHpr[0] = self.spawnHpr[1] - 90
            self.spawnHpr[1] = -tmp
        if props.hasAttribute("TeamNum"):
            self.team = props.getAttributeValue("TeamNum").getInt()
        if props.hasAttribute("round_bluespawn"):
            self.blueCPRoundName = props.getAttributeValue("round_bluespawn").getString()
        if props.hasAttribute("round_redspawn"):
            self.redCPRoundName = props.getAttributeValue("round_redspawn").getString()

    def announceGenerate(self):
        EntityBase.announceGenerate(self)
        if self.redCPRoundName:
            self.redCPRound = base.entMgr.findExactEntity(self.redCPRoundName)
        if self.blueCPRoundName:
            self.blueCPRound = base.entMgr.findExactEntity(self.blueCPRoundName)

    def delete(self):
        self.redCPRound = None
        self.blueCPRound = None
        self.controlPoint = None
        EntityBase.delete(self)

    def input_Disable(self, caller):
        self.enabled = False

    def input_Enable(self, caller):
        self.enabled = True

    def input_TurnOn(self, caller):
        self.enabled = True

    def input_TurnOff(self, caller):
        self.enabled = False

    def input_Toggle(self, caller):
        self.enabled = not self.enabled

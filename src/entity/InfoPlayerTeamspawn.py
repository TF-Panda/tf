"""InfoPlayerTeamspawn module: contains the InfoPlayerTeamspawn class."""

from panda3d.core import *

from .EntityBase import EntityBase
from tf.tfbase import TFGlobals

class InfoPlayerTeamspawn(EntityBase):

    def __init__(self):
        EntityBase.__init__(self)
        self.team = TFGlobals.TFTeam.NoTeam
        self.spawnPos = Point3()
        self.spawnHpr = Vec3()
        self.enabled = True

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
            self.team = props.getAttributeValue("TeamNum").getInt() - 2

    def input_Disable(self, caller):
        self.enabled = False

    def input_Enable(self, caller):
        self.enabled = True

    def input_Toggle(self, caller):
        self.enabled = not self.enabled

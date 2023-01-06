"""TeamControlPoint module: contains the TeamControlPoint class."""

from .DistributedEntity import DistributedEntity
from tf.actor.Model import Model
from tf.tfbase import TFGlobals

class TeamControlPoint(DistributedEntity):

    def __init__(self):
        DistributedEntity.__init__(self)
        self.teamPreviousPoint = {}
        self.ownerTeam = TFGlobals.TFTeam.NoTeam
        self.defaultOwner = TFGlobals.TFTeam.NoTeam
        self.pointIndex = 0
        self.pointGroup = 0
        self.hologramModel = None

    if IS_CLIENT:
        def RecvProxy_ownerTeam(self, team):
            self.ownerTeam = team
            self.updateHologramNode()

        def updateHologramNode(self):
            if self.hologramModel:
                self.hologramModel.setBodygroupValue("switch", self.ownerTeam + 1)
    else:
        def initFromLevel(self, ent, props):
            DistributedEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("point_default_owner"):
                self.ownerTeam = props.getAttributeValue("point_default_owner").getInt() - 2
                self.defaultOwner = self.ownerTeam
            if props.hasAttribute("point_index"):
                self.pointIndex = props.getAttributeValue("point_index").getInt()
            if props.hasAttribute("point_group"):
                self.pointGroup = props.getAttributeValue("point_group").getInt()

        def capturedByTeam(self, team):
            self.ownerTeam = team
            messenger.send('controlPointCapped', [self])

        def teamStartCapping(self, team):
            base.game.enemySound("Announcer.ControlPointContested", team)

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        if IS_CLIENT:
            self.hologramModel = Model()
            self.hologramModel.loadModel("models/effects/cappoint_hologram", flatten=False)
            self.hologramModel.modelNp.reparentTo(self)
            self.updateHologramNode()
            self.spinIval = self.hologramModel.modelNp.hprInterval(5.0, (360, 0, 0), (0, 0, 0))
            self.spinIval.loop()

            self.ls()

    def disable(self):
        if IS_CLIENT:
            self.spinIval.finish()
            self.spinIval = None
            self.hologramModel.cleanup()
            self.hologramModel = None
        DistributedEntity.disable(self)

if not IS_CLIENT:
    TeamControlPointAI = TeamControlPoint
    TeamControlPointAI.__name__ = 'TeamControlPointAI'

"""TeamControlPoint module: contains the TeamControlPoint class."""

from .DistributedEntity import DistributedEntity
from tf.actor.Model import Model
from tf.tfbase import TFGlobals

class TeamControlPoint(DistributedEntity):

    def __init__(self):
        DistributedEntity.__init__(self)
        self.teamPreviousPointNames = {}
        self.teamPreviousPoints = {}
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
            if props.hasAttribute("team_previouspoint_2_0"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Red] = [props.getAttributeValue("team_previouspoint_2_0").getString()]
            if props.hasAttribute("team_previouspoint_2_1"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Red].append(props.getAttributeValue("team_previouspoint_2_1").getString())
            if props.hasAttribute("team_previouspoint_2_2"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Red].append(props.getAttributeValue("team_previouspoint_2_2").getString())
            if props.hasAttribute("team_previouspoint_2_3"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Red].append(props.getAttributeValue("team_previouspoint_2_3").getString())
            if props.hasAttribute("team_previouspoint_3_0"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Blue] = [props.getAttributeValue("team_previouspoint_3_0").getString()]
            if props.hasAttribute("team_previouspoint_3_1"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Blue].append(props.getAttributeValue("team_previouspoint_3_1").getString())
            if props.hasAttribute("team_previouspoint_3_2"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Blue].append(props.getAttributeValue("team_previouspoint_3_2").getString())
            if props.hasAttribute("team_previouspoint_3_3"):
                self.teamPreviousPointNames[TFGlobals.TFTeam.Blue].append(props.getAttributeValue("team_previouspoint_3_3").getString())

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
        else:
            # Get the points necessary to be captured to before capping this point.
            for team in self.teamPreviousPointNames.keys():
                self.teamPreviousPoints[team] = []
                for pointName in self.teamPreviousPointNames[team]:
                    self.teamPreviousPoints[team].append(base.entMgr.findExactEntity(pointName))

    def disable(self):
        if IS_CLIENT:
            self.spinIval.finish()
            self.spinIval = None
            self.hologramModel.cleanup()
            self.hologramModel = None
        self.teamPreviousPointNames = None
        self.teamPreviousPoints = None
        DistributedEntity.disable(self)

if not IS_CLIENT:
    TeamControlPointAI = TeamControlPoint
    TeamControlPointAI.__name__ = 'TeamControlPointAI'

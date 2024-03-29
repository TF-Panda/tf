"""TeamControlPoint module: contains the TeamControlPoint class."""

from tf.actor.Model import Model
from tf.tfbase import TFGlobals

from . import CapState
from .DistributedEntity import DistributedEntity


class TeamControlPoint(DistributedEntity):

    def __init__(self):
        DistributedEntity.__init__(self)
        self.teamPreviousPointNames = {}
        self.teamPreviousPoints = {}
        self.ownerTeam = TFGlobals.TFTeam.NoTeam
        self.teamProgress = TFGlobals.TFTeam.NoTeam
        self.capProgress = 0.0
        self.defaultOwner = TFGlobals.TFTeam.NoTeam
        self.pointIndex = 0
        self.pointGroup = 0
        self.hologramModel = None
        self.pointName = ""
        self.capperCount = 0
        self.capState = CapState.CSIdle

    if IS_CLIENT:
        def RecvProxy_ownerTeam(self, team):
            if team != self.ownerTeam:
                self.ownerTeam = team
                self.updateHologramNode()
                messenger.send('ControlPointOwnerTeamChanged', [self])

        def RecvProxy_capProgress(self, prog):
            if prog != self.capProgress:
                self.capProgress = prog
                messenger.send('ControlPointProgressChanged', [self])

        def RecvProxy_capperCount(self, count):
            if count != self.capperCount:
                self.capperCount = count
                messenger.send('ControlPointCapperCountChanged', [self])

        def RecvProxy_capState(self, state):
            if state != self.capState:
                self.capState = state
                messenger.send('ControlPointCapperCountChanged', [self])

        def RecvProxy_teamProgress(self, team):
            if team != self.teamProgress:
                self.teamProgress = team
                messenger.send('ControlPointTeamProgressChanged', [self])

        def updateHologramNode(self):
            if self.hologramModel:
                if self.ownerTeam == TFGlobals.TFTeam.NoTeam:
                    switch = 0
                elif self.ownerTeam == TFGlobals.TFTeam.Red:
                    switch = 1
                elif self.ownerTeam == TFGlobals.TFTeam.Blue:
                    switch = 2
                else:
                    switch = 0
                self.hologramModel.setBodygroupValue("switch", switch)
    else:
        def initFromLevel(self, ent, props):
            DistributedEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("point_default_owner"):
                self.ownerTeam = props.getAttributeValue("point_default_owner").getInt()
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
            if props.hasAttribute("point_printname"):
                self.pointName = props.getAttributeValue("point_printname").getString()

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
                    ent = base.entMgr.findExactEntity(pointName)
                    if ent != self:
                        # Don't depend on ourselves.
                        self.teamPreviousPoints[team].append(ent)

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

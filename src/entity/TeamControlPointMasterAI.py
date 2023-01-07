"""TeamControlPointMasterAI module: contains the TeamControlPointMasterAI class."""

from .EntityBase import EntityBase
from direct.distributed2.DistributedObjectAI import DistributedObjectAI

from tf.tfbase import TFGlobals

class TeamControlPointMasterAI(DistributedObjectAI, EntityBase):

    RestrictNeither = 0
    RestrictBoth = 1
    RestrictRed = 2
    RestrictBlue = 3

    def __init__(self):
        DistributedObjectAI.__init__(self)
        EntityBase.__init__(self)
        self.rounds = []
        self.points = []
        self.roundIndex = -1
        # If not NoTeam, only this team can win by capping all the points.
        self.restrictWinTeam = self.RestrictNeither
        self.switchTeams = False

        self.pointDoIds = []
        self.pointLayout = []

    def areAllPointsIdle(self):
        for p in self.points:
            if p.capProgress > 0 and p.capProgress < 1:
                return False
        return True

    def isNetworkedEntity(self):
        return True

    def initFromLevel(self, ent, props):
        EntityBase.initFromLevel(self, ent, props)
        if props.hasAttribute("cpm_restrict_team_cap_win"):
            self.restrictWinTeam = props.getAttributeValue("cpm_restrict_team_cap_win").getInt()
        if props.hasAttribute("switch_teams"):
            self.switchTeams = props.getAttributeValue("switch_teams").getBool()

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        EntityBase.announceGenerate(self)

        base.game.controlPointMaster = self

        self.rounds = base.entMgr.findAllEntitiesByClassName("team_control_point_round")
        self.points = base.entMgr.findAllEntitiesByClassName("team_control_point")
        # Sort points by index.
        self.points.sort(key=lambda x: x.pointIndex)
        self.pointDoIds = [x.doId for x in self.points]
        self.pointLayout = [i for i in range(len(self.points))]
        self.accept('controlPointCapped', self.onPointCapped)

    def delete(self):
        self.rounds = None
        self.points = None
        self.pointDoIds = None
        self.pointLayout = None
        self.ignore('controlPointCapped')
        base.game.controlPointMaster = None
        EntityBase.delete(self)
        DistributedObjectAI.delete(self)

    def checkWinner(self):
        if self.restrictWinTeam == self.RestrictBoth:
            return

        winTeam = None
        for p in self.points:
            if winTeam is None:
                winTeam = p.ownerTeam
            elif winTeam != p.ownerTeam:
                winTeam = None
                break

        if winTeam is None:
            return

        if self.restrictWinTeam != self.RestrictNeither:
            if self.restrictWinTeam == self.RestrictRed and winTeam == TFGlobals.TFTeam.Red:
                return
            elif self.restrictWinTeam == self.RestrictBlue and winTeam == TFGlobals.TFTeam.Blue:
                return

        # This team wins.
        base.game.endRound(winTeam)
        base.game.switchTeamsOnNewRound = self.switchTeams
        base.game.forceMapReset = True # TODO

    def onPointCapped(self, point):
        """
        Called by a team_control_point when it gets capped.
        """

        assert point in self.points

        # Check if all points are owned by one team, if so, that team wins.
        self.checkWinner()

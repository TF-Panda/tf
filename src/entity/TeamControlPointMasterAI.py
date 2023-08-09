"""TeamControlPointMasterAI module: contains the TeamControlPointMasterAI class."""

from direct.distributed2.DistributedObjectAI import DistributedObjectAI
from tf.tfbase import TFGlobals

from .TeamControlPointManagerAI import TeamControlPointManagerAI


class TeamControlPointMasterAI(DistributedObjectAI, TeamControlPointManagerAI):

    def __init__(self):
        DistributedObjectAI.__init__(self)
        TeamControlPointManagerAI.__init__(self)

        self.rounds = []
        self.currentRound = None
        self.roundIndex = -1
        self.lastCapTime = 0.0

        self.switchTeams = False

        self.pointDoIds = []
        self.pointLayout = []

    def canTeamWin(self, team):
        if self.currentRound:
            return self.currentRound.canTeamWin(team)
        return TeamControlPointManagerAI.canTeamWin(self, team)

    def onNewRound(self):
        """
        Messenger hook when the game manager starts a new round.
        """

        # If we have rounds, switch to the next round.
        if self.rounds:
            ret = self.nextRound()

            # When the previous round ended, we checked that there
            # is another round to play.  So this shouldn't fail.
            assert ret

    def areAllPointsIdle(self):
        if self.currentRound:
            ret = self.currentRound.areAllPointsIdle()
        else:
            ret = TeamControlPointManagerAI.areAllPointsIdle(self)

        # Points are idle if they all have full or no progress, and a point
        # hasn't been capped recently.  (Works around entity I/O race condition).
        return ret and (base.clockMgr.getTime() - self.lastCapTime) >= 0.1

    def setRound(self, index):
        assert self.rounds and not self.points
        self.roundIndex = index
        r = self.rounds[index]
        self.currentRound = r
        self.pointDoIds = [x.doId for x in r.points]
        self.pointLayout = [i for i in range(len(self.pointDoIds))]

    def hasNextRound(self):
        """
        Returns True if there is another round to play after this one, or
        False if this is the last round.
        """
        return (self.roundIndex + 1) < len(self.rounds)

    def nextRound(self):
        """
        Switches the master to the next control point round.
        Returns True if the switch was made, or False if there are no more
        rounds to play.
        """
        index = self.roundIndex + 1
        if index >= len(self.rounds):
            return False
        self.setRound(index)
        return True

    def isNetworkedEntity(self):
        return True

    def initFromLevel(self, ent, props):
        TeamControlPointManagerAI.initFromLevel(self, ent, props)
        if props.hasAttribute("cpm_restrict_team_cap_win"):
            self.restrictWinTeam = props.getAttributeValue("cpm_restrict_team_cap_win").getInt()
        if props.hasAttribute("switch_teams"):
            self.switchTeams = props.getAttributeValue("switch_teams").getBool()

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        TeamControlPointManagerAI.announceGenerate(self)

        base.game.controlPointMaster = self

        self.rounds = base.entMgr.findAllEntitiesByClassName("team_control_point_round")
        if not self.rounds:
            self.points = base.entMgr.findAllEntitiesByClassName("team_control_point")
            # Sort points by index.
            self.points.sort(key=lambda x: x.pointIndex)
            self.pointDoIds = [x.doId for x in self.points]
            self.pointLayout = [i for i in range(len(self.points))]
        else:
            # Sort rounds by decreasing priority number.
            self.rounds.sort(key=lambda x: x.roundPriority, reverse=True)

        self.accept('controlPointCapped', self.onPointCapped)
        self.accept('OnNewRound', self.onNewRound)

    def delete(self):
        self.rounds = None
        self.points = None
        self.pointDoIds = None
        self.pointLayout = None
        self.ignore('controlPointCapped')
        base.game.controlPointMaster = None
        TeamControlPointManagerAI.delete(self)
        DistributedObjectAI.delete(self)

    def checkWinner(self):
        if self.currentRound:
            winTeam = self.currentRound.checkWinner()
        else:
            winTeam = TeamControlPointManagerAI.checkWinner(self)

        if winTeam is not None:
            isFinalRound = (not self.rounds or not self.hasNextRound())
            # This team wins.
            base.game.endRound(winTeam, TFGlobals.WinReason.CapturedPoints if isFinalRound else TFGlobals.WinReason.SeizedArea)
            if isFinalRound:
                # This is the end of the full round, so switch teams
                # and restart.
                base.game.switchTeamsOnNewRound = self.switchTeams
                base.game.forceMapReset = True #TODO
            else:
                # There is another CP round to play, so don't switch teams
                # or reset.
                base.game.switchTeamsOnNewRound = False
                base.game.forceMapReset = False

    def onPointCapped(self, point):
        """
        Called by a team_control_point when it gets capped.
        """

        #assert point in self.points

        self.lastCapTime = base.clockMgr.getTime()

        # Check if all points are owned by one team, if so, that team wins.
        self.checkWinner()

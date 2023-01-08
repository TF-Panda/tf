"""TeamControlPointRoundAI module: contains the TeamControlPointRoundAI class."""

from .TeamControlPointMasterAI import TeamControlPointManagerAI

class TeamControlPointRoundAI(TeamControlPointManagerAI):

    def __init__(self):
        TeamControlPointManagerAI.__init__(self)
        self.pointNames = []
        self.roundPriority = 0
        self.isActiveRound = False

    def initFromLevel(self, ent, props):
        TeamControlPointManagerAI.initFromLevel(self, ent, props)

        if props.hasAttribute("cpr_priority"):
            self.roundPriority = props.getAttributeValue("cpr_priority").getInt()

        if props.hasAttribute("cpr_cp_names"):
            self.pointNames = props.getAttributeValue("cpr_cp_names").getString().split()

        if props.hasAttribute("cpr_restrict_team_cap_win"):
            self.restrictWinTeam = props.getAttributeValue("cpr_restrict_team_cap_win").getInt()

    def announceGenerate(self):
        TeamControlPointManagerAI.announceGenerate(self)

        for targetName in self.pointNames:
            self.points.append(base.entMgr.findExactEntity(targetName))

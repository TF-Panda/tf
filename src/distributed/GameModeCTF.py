"""GameModeCTF module: contains the GameModeCTF class."""

from tf.tfbase.TFGlobals import TFTeam

from .RoundState import RoundState

class GameModeCTF:

    def __init__(self, gameMgr):
        self.gameMgr = gameMgr

        self.needsSetup = False
        self.setupTime = 1.0

        # Number of times team has to cap to win.
        self.winCapCount = 3
        self.teamCapCounts = {
          TFTeam.Red  : 0,
          TFTeam.Blue : 0,
        }

    def canPickupFlag(self):
        return self.gameMgr.roundState == RoundState.Playing

    def flagCaptured(self, team):
        self.teamCapCounts[team] += 1
        if self.teamCapCounts[team] >= self.winCapCount:
            # This team wins.
            self.gameMgr.endRound(team)
            return True
        return False

    def returnFlags(self):
        from tf.entity.DistributedTeamFlagAI import DistributedTeamFlagAI
        for do in base.air.doId2do.values():
            if isinstance(do, DistributedTeamFlagAI):
                do.returnFlag(False, False)

    def onNewRound(self):
        # Reset team cap counts.
        self.teamCapCounts[TFTeam.Red] = 0
        self.teamCapCounts[TFTeam.Blue] = 0
        self.returnFlags()

    def onBeginRound(self):
        pass

    def onEndRound(self):
        # Return the flags.
        self.returnFlags()

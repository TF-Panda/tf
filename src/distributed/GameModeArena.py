"""GameModeArena module: contains the GameModeArena class."""

class GameModeArena:

    def __init__(self, gameMgr):
        self.gameMgr = gameMgr

        self.needsSetup = False
        self.setupTime = 0.0
        self.preRoundTime = 5.0
        self.arenaLogicEnt = None

    def onNewRound(self):
        pass

    def onBeginRound(self):
        if self.arenaLogicEnt:
            self.arenaLogicEnt.connMgr.fireOutput("OnArenaRoundStart")

    def onEndRound(self):
        pass

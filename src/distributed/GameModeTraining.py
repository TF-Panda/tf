"""GameModeTraining module: contains the GameModeTraining class."""

class GameModeTraining:

    def __init__(self, gameMgr):
        self.gameMgr = gameMgr

        self.needsSetup = False
        self.setupTime = 60.0

    def onNewRound(self):
        pass

    def onBeginRound(self):
        pass

    def onEndRound(self):
        pass

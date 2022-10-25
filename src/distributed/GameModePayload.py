"""GameModePayload module: contains the GameModePayload class."""

class GameModePayload:

    def __init__(self, gameMgr):
        self.gameMgr = gameMgr

        self.needsSetup = True
        self.setupTime = 60.0

    def onNewRound(self):
        pass

    def onBeginRound(self):
        pass

    def onEndRound(self):
        pass

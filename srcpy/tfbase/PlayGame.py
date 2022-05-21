from direct.fsm.StateData import StateData
from direct.fsm.FSM import FSM

class PlayGame(StateData, FSM):

    def __init__(self):
        self.cr = None

    def load(self):
        self.cr = TFClientRepository()

    def enter(self, connectInfo):



from tf.character.DistributedCharAI import DistributedCharAI

from .DViewModelShared import DViewModelShared
from tf.character.Activity import Activity

class DViewModelAI(DistributedCharAI):

    def __init__(self):
        DistributedCharAI.__init__(self)
        DViewModelShared.__init__(self)

    def delete(self):
        if self.player:
            self.player.viewModel = None
            self.player = None

    def setPlayerId(self, playerId):
        self.playerId = playerId
        self.player = base.sv.doId2do.get(self.playerId)
        self.player.viewModel = self
        self.setModel(self.player.classInfo.ViewModel)

    def generate(self):
        DistributedCharAI.generate(self)
        # Set to the idle sequence by default.
        self.setSequence(self.getSequenceForActivity(Activity.Primary_VM_Idle))

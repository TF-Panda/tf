
from tf.actor.DistributedCharAI import DistributedCharAI

from .DViewModelShared import DViewModelShared
from tf.actor.Activity import Activity

class DViewModelAI(DistributedCharAI):

    def __init__(self):
        DistributedCharAI.__init__(self)
        DViewModelShared.__init__(self)
        self.clientSideAnimation = True

    def delete(self):
        if self.player:
            self.player.viewModel = None
            self.player = None
        DistributedCharAI.delete(self)

    def setPlayerId(self, playerId):
        self.playerId = playerId
        self.player = base.sv.doId2do.get(self.playerId)
        self.player.viewModel = self
        self.setModel(self.player.classInfo.ViewModel)

    def generate(self):
        DistributedCharAI.generate(self)
        # Set to the idle sequence by default.
        self.startChannel(act=Activity.Primary_VM_Idle)

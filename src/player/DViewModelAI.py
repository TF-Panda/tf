
from tf.actor.Activity import Activity
from tf.actor.DistributedCharAI import DistributedCharAI
from tf.tfbase import TFGlobals

from .DViewModelShared import DViewModelShared


class DViewModelAI(DistributedCharAI):

    def __init__(self):
        DistributedCharAI.__init__(self)
        DViewModelShared.__init__(self)
        self.clientSideAnimation = True
        # ViewModel of another player is hidden to them,
        # but the local avatar parents its viewmodel to the viewmodel
        # scene graph.
        self.parentEntityId = TFGlobals.WorldParent.Unchanged

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
        self.setAnim(activity=Activity.Primary_VM_Idle)

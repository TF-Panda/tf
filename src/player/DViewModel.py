
from tf.character.DistributedChar import DistributedChar

from .DViewModelShared import DViewModelShared

from panda3d.core import *

class DViewModel(DistributedChar, DViewModelShared):

    def __init__(self):
        DistributedChar.__init__(self)
        DViewModelShared.__init__(self)

    #def update(self):
    #    DistributedChar.update(self)

    #    if self.character:
    #        self.character.update()
    #        print("VM anim time", self.seqPlayer.getAnimTime())
    #        print("VM cycle:", self.seqPlayer.getCycle())

    def shouldPredict(self):
        if self.playerId == base.localAvatarId:
            return True
        return DistributedChar.shouldPredict(self)

    def disable(self):
        if self.player:
            self.player.viewModel = None
            self.player = None
        if self.playerId == base.localAvatarId:
            self.reparentTo(hidden)
        DistributedChar.disable(self)

    def RecvProxy_playerId(self, playerId):
        self.playerId = playerId
        self.player = base.cr.doId2do.get(self.playerId)
        self.player.viewModel = self
        if self.playerId == base.localAvatarId:
            self.reparentTo(base.vmCamera)
        else:
            self.reparentTo(hidden)

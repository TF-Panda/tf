
from tf.character.DistributedChar import DistributedChar

from .DistributedWeaponShared import DistributedWeaponShared

class DistributedWeapon(DistributedChar, DistributedWeaponShared):

    def __init__(self):
        DistributedChar.__init__(self)
        DistributedWeaponShared.__init__(self)

    def delete(self):
        DistributedChar.delete(self)
        DistributedWeaponShared.delete(self)

    def generate(self):
        DistributedChar.generate(self)
        DistributedWeaponShared.generate(self)

    def isOwnedByLocalPlayer(self):
        return self.playerId == base.localAvatarId

    def isActiveLocalPlayerWeapon(self):
        return self.isOwnedByLocalPlayer() and (base.localAvatar.weapons[base.localAvatar.activeWeapon] == self.doId)

    def RecvProxy_ammo(self, ammo):
        self.ammo = ammo
        if self.isActiveLocalPlayerWeapon():
            base.localAvatar.hud.updateAmmoLabel()

    def RecvProxy_clip(self, clip):
        self.clip = clip
        if self.isActiveLocalPlayerWeapon():
            base.localAvatar.hud.updateAmmoLabel()

    def RecvProxy_playerId(self, playerId):
        self.playerId = playerId
        if self.playerId != -1:
            self.player = base.cr.doId2do.get(playerId)
            self.viewModel = self.player.viewModel
        else:
            self.player = None
            self.viewModel = None

    def activate(self):
        """
        Called when the weapon becomes the active weapon.
        """

        assert self.player

        # Parent the world model to the player.
        self.modelNp.reparentTo(self.player.modelNp)
        self.setJointMergeCharacter(self.player.character)

        # Parent the view model to the player's view model.
        self.viewModelChar.modelNp.reparentTo(self.player.viewModel.modelNp)
        self.viewModelChar.setJointMergeCharacter(self.player.viewModel.character)

        if self.isActiveLocalPlayerWeapon():
            base.localAvatar.hud.updateAmmoLabel()

    def deactivate(self):
        """
        Called when the weapon is no longer the active weapon.
        """
        assert self.player

        self.modelNp.reparentTo(hidden)
        self.viewModelChar.modelNp.reparentTo(hidden)

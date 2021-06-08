
from tf.character.DistributedChar import DistributedChar

from .DistributedWeaponShared import DistributedWeaponShared

class DistributedWeapon(DistributedChar, DistributedWeaponShared):

    def __init__(self):
        DistributedChar.__init__(self)
        DistributedWeaponShared.__init__(self)

        # Fields we predict locally.
        self.addPredictionField("nextPrimaryAttack", float, tolerance=0.001)
        self.addPredictionField("nextSecondaryAttack", float, tolerance=0.001)
        self.addPredictionField("timeWeaponIdle", float, tolerance=0.001)
        self.addPredictionField("ammo", int, setter=self.setAmmo)
        self.addPredictionField("ammo2", int)
        self.addPredictionField("clip", int, setter=self.setClip)
        self.addPredictionField("clip2", int)
        self.addPredictionField("inReload", bool, networked=False)
        self.addPredictionField("fireOnEmpty", bool, networked=False)
        self.addPredictionField("nextEmptySoundTime", float, networked=False)
        self.addPredictionField("activity", int, networked=False)
        self.addPredictionField("fireDuration", float, networked=False)
        self.addPredictionField("reloadsSingly", bool, networked=False)

    def shouldPredict(self):
        if self.isOwnedByLocalPlayer():
            return True
        return DistributedChar.shouldPredict(self)

    def delete(self):
        DistributedChar.delete(self)
        DistributedWeaponShared.delete(self)

    def generate(self):
        DistributedChar.generate(self)
        DistributedWeaponShared.generate(self)

    def isOwnedByLocalPlayer(self):
        return self.playerId == base.localAvatarId

    def isActiveLocalPlayerWeapon(self):
        if (base.localAvatar.activeWeapon < 0) or (base.localAvatar.activeWeapon >= len(base.localAvatar.weapons)):
            return False

        return self.isOwnedByLocalPlayer() and (base.localAvatar.weapons[base.localAvatar.activeWeapon] == self.doId)

    def setAmmo(self, ammo):
        self.ammo = ammo
        if self.isActiveLocalPlayerWeapon():
            base.localAvatar.hud.updateAmmoLabel()

    def RecvProxy_ammo(self, ammo):
        self.setAmmo(ammo)

    def setClip(self, clip):
        self.clip = clip
        if self.isActiveLocalPlayerWeapon():
            base.localAvatar.hud.updateAmmoLabel()

    def RecvProxy_clip(self, clip):
        self.setClip(clip)

    def RecvProxy_playerId(self, playerId):
        self.setPlayerId(playerId)

    def activate(self):
        """
        Called when the weapon becomes the active weapon.
        """

        assert self.player

        DistributedWeaponShared.activate(self)

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

        DistributedWeaponShared.deactivate(self)

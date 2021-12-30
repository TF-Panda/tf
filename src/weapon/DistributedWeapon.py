
from tf.actor.DistributedChar import DistributedChar

from .DistributedWeaponShared import DistributedWeaponShared

from tf.tfbase import Sounds

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

    def playSound(self, soundName):
        """
        Plays predicted client-side weapon sound.
        """

        if not base.cr.prediction.firstTimePredicted:
            # We've already predicted this command, so don't play sounds again.
            return

        if len(soundName) == 0:
            return

        pos = self.player.getEyePosition()
        snd = Sounds.createSoundByName(soundName)
        if not snd:
            return
        snd.set3dAttributes(pos[0], pos[1], pos[2], 0.0, 0.0, 0.0)
        snd.play()

    def addViewModelBob(self, viewModel, info):
        pass

    def shouldPredict(self):
        if self.isOwnedByLocalPlayer():
            return True
        return DistributedChar.shouldPredict(self)
        #return False

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

    def update(self):
        DistributedChar.update(self)

        # Poll for the player.
        if self.playerId != -1 and (self.player is None or self.viewModel is None):
            self.updatePlayer()

    def updatePlayer(self):
        DistributedWeaponShared.updatePlayer(self)

        if self.player and self.player.hasActiveWeapon() and \
            self.player.weapons[self.player.activeWeapon] == self.doId:
            self.active = True
        else:
            self.active = False

        if self.active and self.player and self.player.character:
            # Make sure the world model is parented to the player.
            self.reparentTo(self.player)
            self.setJointMergeCharacter(self.player.character)

            if self.isActiveLocalPlayerWeapon() and self.player.viewModel:
                # Parent the view model to the player's view model.
                self.viewModelChar.reparentTo(self.player.viewModel)
                self.viewModelChar.setJointMergeCharacter(self.player.viewModel.character)

    def activate(self):
        """
        Called when the weapon becomes the active weapon.
        """

        assert self.player

        self.active = True

        if self.isActiveLocalPlayerWeapon():
            DistributedWeaponShared.activate(self)

        # Parent the world model to the player.
        self.reparentTo(self.player)
        self.setJointMergeCharacter(self.player.character)

        # Parent the view model to the player's view model.
        self.viewModelChar.reparentTo(self.player.viewModel)
        self.viewModelChar.setJointMergeCharacter(self.player.viewModel.character)

        if self.isActiveLocalPlayerWeapon():
            base.localAvatar.hud.updateAmmoLabel()

    def deactivate(self):
        """
        Called when the weapon is no longer the active weapon.
        """
        assert self.player

        self.active = False

        self.reparentTo(hidden)
        self.viewModelChar.reparentTo(hidden)

        if self.isActiveLocalPlayerWeapon():
            DistributedWeaponShared.deactivate(self)

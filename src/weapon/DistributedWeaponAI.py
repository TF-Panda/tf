
from tf.actor.DistributedCharAI import DistributedCharAI
from .DistributedWeaponShared import DistributedWeaponShared

class DistributedWeaponAI(DistributedCharAI, DistributedWeaponShared):

    def __init__(self):
        DistributedCharAI.__init__(self)
        DistributedWeaponShared.__init__(self)
        self.clientSideAnimation = True

        self.active = False

    def updatePlayer(self):
        DistributedWeaponShared.updatePlayer(self)
        # Be on same team as player and use team-colored skin for
        # weapon model.
        self.team = self.player.team
        self.skin = self.player.skin

    def activate(self):
        self.active = True

        if self.UsesViewModel:
            self.player.viewModel.setModel(self.WeaponViewModel)

        DistributedWeaponShared.activate(self)
        if not self.HideWeapon:
            # Parent the world model to the player.
            self.reparentTo(self.player.modelNp)
            self.setJointMergeCharacter(self.player.character)

    def deactivate(self):
        self.active = False

        self.reparentTo(base.hidden)
        if self.UsesViewModel and self.player and self.player.viewModel:
            self.player.viewModel.setModel(self.player.classInfo.ViewModel)
        DistributedWeaponShared.deactivate(self)

    def playSound(self, soundName, predicted=True):
        """
        Emits the indicated sound from this weapon entity.  If predicted is
        True, the sound event is not broadcasted to the client that is using
        this weapon, and is assumed that the client is predicting the sound.
        """

        if len(soundName) == 0:
            return

        if predicted:
            # If the client using the weapon is predicting this sound, don't
            # send the sound event to them.
            exclude = [self.player.owner]
        else:
            exclude = []

        # Only the AI side, don't send the sound to the player that is using
        # weapon, as they should have already predicted the sound.

        # Make it spatial for other players, non-spatial for the player.
        offset = self.player.getWorldSpaceCenter() - self.getPos(base.render)
        if not predicted:
            self.emitSound(soundName, client=self.player.owner)
        self.emitSoundSpatial(soundName, offset, excludeClients=exclude)

    def delete(self):
        if self.active:
            self.deactivate()

        DistributedCharAI.delete(self)
        DistributedWeaponShared.delete(self)

    def generate(self):
        DistributedCharAI.generate(self)
        DistributedWeaponShared.generate(self)
        self.setModel(self.WeaponModel)

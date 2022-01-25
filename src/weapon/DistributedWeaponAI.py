
from tf.actor.DistributedCharAI import DistributedCharAI
from .DistributedWeaponShared import DistributedWeaponShared

class DistributedWeaponAI(DistributedCharAI, DistributedWeaponShared):

    def __init__(self):
        DistributedCharAI.__init__(self)
        DistributedWeaponShared.__init__(self)
        self.clientSideAnimation = True

    def activate(self):
        DistributedWeaponShared.activate(self)
        # Parent the world model to the player.
        self.reparentTo(self.player.modelNp)
        self.setJointMergeCharacter(self.player.character)

    def deactivate(self):
        self.reparentTo(base.hidden)
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
        base.net.game.d_emitSound(soundName, self.player.getWorldSpaceCenter(), excludeClients=exclude)

    def delete(self):
        DistributedCharAI.delete(self)
        DistributedWeaponShared.delete(self)

    def generate(self):
        DistributedCharAI.generate(self)
        DistributedWeaponShared.generate(self)
        self.setModel(self.WeaponModel)

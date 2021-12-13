
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

    def playSound(self, soundName):
        if len(soundName) == 0:
            return

        base.net.game.d_emitSound(soundName, self.player.getWorldSpaceCenter())

    def delete(self):
        DistributedCharAI.delete(self)
        DistributedWeaponShared.delete(self)

    def generate(self):
        DistributedCharAI.generate(self)
        DistributedWeaponShared.generate(self)
        self.setModel(self.WeaponModel)


from tf.character.DistributedCharAI import DistributedCharAI
from .DistributedWeaponShared import DistributedWeaponShared

class DistributedWeaponAI(DistributedCharAI, DistributedWeaponShared):

    def __init__(self):
        DistributedCharAI.__init__(self)
        DistributedWeaponShared.__init__(self)

    def playSound(self, soundName):
        if len(soundName) == 0:
            return

        base.net.game.d_emitSound(soundName, self.player.getPos() + (0, 0, self.player.classInfo.ViewHeight / 2))

    def delete(self):
        DistributedCharAI.delete(self)
        DistributedWeaponShared.delete(self)

    def generate(self):
        DistributedCharAI.generate(self)
        DistributedWeaponShared.generate(self)
        self.setModel(self.WeaponModel)

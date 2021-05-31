
from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponMode

class DShotgunShared:

    def __init__(self):
        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = True

    def getName(self):
        return TFLocalizer.Shotgun

    def getSingleSound(self):
        return "Weapon_Shotgun.Single"

    def getEmptySound(self):
        return "Weapon_Shotgun.Empty"

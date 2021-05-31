
from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponType

class DWrenchShared:

    def __init__(self):
        self.usesAmmo = False
        self.usesClip = False
        self.meleeWeapon = True
        self.reloadsSingly = False

        self.weaponType = TFWeaponType.Melee

    def getName(self):
        return TFLocalizer.Wrench

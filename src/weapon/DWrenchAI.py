
from .TFWeaponAI import TFWeaponAI

from .DWrenchShared import DWrenchShared

from tf.character.Activity import Activity

class DWrenchAI(TFWeaponAI, DWrenchShared):

    WeaponModel = "tfmodels/src/weapons/wrench/c_wrench.pmdl"
    WeaponViewModel = "tfmodels/src/weapons/wrench/c_wrench.pmdl"

    def __init__(self):
        TFWeaponAI.__init__(self)
        DWrenchShared.__init__(self)

        self.primaryAttackInterval = 1.0

    def getSingleSound(self):
        return "Weapon_Wrench.Miss"

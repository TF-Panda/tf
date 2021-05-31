
from .TFWeapon import TFWeapon

from .DWrenchShared import DWrenchShared

class DWrench(TFWeapon, DWrenchShared):

    WeaponViewModel = "tfmodels/src/weapons/wrench/c_wrench.pmdl"

    def __init__(self):
        TFWeapon.__init__(self)
        DWrenchShared.__init__(self)

    def getName(self):
        return DWrenchShared.getName(self)

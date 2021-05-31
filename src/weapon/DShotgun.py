
from .TFWeapon import TFWeapon

from .DShotgunShared import DShotgunShared

class DShotgun(TFWeapon, DShotgunShared):

    WeaponViewModel = "tfmodels/src/weapons/shotgun/c_shotgun.pmdl"

    def __init__(self):
        TFWeapon.__init__(self)
        DShotgunShared.__init__(self)

    def getName(self):
        return DShotgunShared.getName(self)

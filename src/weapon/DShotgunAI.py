
from .TFWeapon import TFWeaponAI

from .DShotgunShared import DShotgunShared

class DShotgunAI(TFWeaponAI, DShotgunShared):

    WeaponModel = "tfmodels/src/weapons/shotgun/c_shotgun.pmdl"
    WeaponViewModel = "tfmodels/src/weapons/shotgun/c_shotgun.pmdl"

    def __init__(self):
        TFWeaponAI.__init__(self)
        DShotgunShared.__init__(self)

    def getSingleSound(self):
        return DShotgunShared.getSingleSound(self)

    def getEmptySound(self):
        return DShotgunShared.getEmptySound(self)

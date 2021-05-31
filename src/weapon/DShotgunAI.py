
from .TFWeaponAI import TFWeaponAI

from .DShotgunShared import DShotgunShared

class DShotgunAI(TFWeaponAI, DShotgunShared):

    WeaponModel = "tfmodels/src/weapons/shotgun/c_shotgun.pmdl"
    WeaponViewModel = "tfmodels/src/weapons/shotgun/c_shotgun.pmdl"

    def __init__(self):
        TFWeaponAI.__init__(self)
        DShotgunShared.__init__(self)
        self.maxAmmo = 32
        self.maxClip = 6
        self.ammo = self.maxAmmo
        self.clip = self.maxClip
        self.primaryAttackInterval = 0.625

    def getSingleSound(self):
        return DShotgunShared.getSingleSound(self)

    def getEmptySound(self):
        return DShotgunShared.getEmptySound(self)

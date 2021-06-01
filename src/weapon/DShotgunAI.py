
from .TFWeaponAI import TFWeaponAI

from .DShotgunShared import DShotgunShared
from .WeaponMode import TFWeaponMode
from tf.tfbase.TFGlobals import DamageType

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
        self.weaponData = {
            TFWeaponMode.Primary: {
                'bulletsPerShot': 10,
                #'range': 1000000,
                'spread': 0.1,
                'damage': 5
            }
        }
        self.damageType = DamageType.Buckshot | DamageType.UseDistanceMod

    def getSingleSound(self):
        return DShotgunShared.getSingleSound(self)

    def getEmptySound(self):
        return DShotgunShared.getEmptySound(self)

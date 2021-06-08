
from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponMode
from tf.tfbase.TFGlobals import DamageType

class DShotgunShared:

    def __init__(self):
        self.usesAmmo = True
        self.usesClip = True
        self.reloadsSingly = True
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

    def getName(self):
        return TFLocalizer.Shotgun

    def getSingleSound(self):
        return "Weapon_Shotgun.Single"

    def getEmptySound(self):
        return "Weapon_Shotgun.Empty"

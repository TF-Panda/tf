from .DShotgun import DShotgun
from .WeaponMode import TFWeaponType

class DShotgunSecondary(DShotgun):

    def __init__(self):
        DShotgun.__init__(self)
        self.weaponType = TFWeaponType.Secondary

if not IS_CLIENT:
    DShotgunSecondaryAI = DShotgunSecondary
    DShotgunSecondaryAI.__name__ = 'DShotgunSecondaryAI'

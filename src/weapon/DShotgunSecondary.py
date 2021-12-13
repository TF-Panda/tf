from .DShotgun import DShotgun
from .WeaponMode import TFWeaponType, TFWeaponMode

class DShotgunSecondary(DShotgun):

    def __init__(self):
        DShotgun.__init__(self)
        self.weaponType = TFWeaponType.Secondary
        # The heavy, soldier, and pyro shotguns (secondary) have a smaller
        # view kick than the engineer shotgun (primary).
        self.weaponData[TFWeaponMode.Primary]['punchAngle'] = 2.0

if not IS_CLIENT:
    DShotgunSecondaryAI = DShotgunSecondary
    DShotgunSecondaryAI.__name__ = 'DShotgunSecondaryAI'

from enum import IntEnum

class PlayerAnimEvent(IntEnum):
    Reload = 0
    ReloadLoop = 1
    ReloadEnd = 2
    AttackPrimary = 3
    AttackSecondary = 4
    AttackGrenade = 5
    Jump = 6

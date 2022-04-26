"""DHealthKitAI module: contains the DHealthKitAI class."""

from .DPickupItemBase import DPickupItemBaseAI

class DHealthKitAI(DPickupItemBaseAI):

    def giveItem(self, ent):
        if ent.health < 1:
            return False

        if not ent.isPlayer():
            # Only for players.
            return False

        maxToGive = max(0, ent.maxHealth - ent.health)
        if maxToGive == 0:
            return False

        ent.health += min(maxToGive, max(1, ent.maxHealth // self.HealthRatio))
        ent.emitSound("HealthKit.Touch", client=ent.owner)

        return True

class DHealthKitSmallAI(DHealthKitAI):
    HealthRatio = 5
    ModelIndex = 5

class DHealthKitMediumAI(DHealthKitAI):
    HealthRatio = 2
    ModelIndex = 4

class DHealthKitFullAI(DHealthKitAI):
    HealthRatio = 1
    ModelIndex = 3

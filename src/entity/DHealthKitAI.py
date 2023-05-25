"""DHealthKitAI module: contains the DHealthKitAI class."""

from .DPickupItemBase import DPickupItemBaseAI

class DHealthKitAI(DPickupItemBaseAI):

    def giveItem(self, ent):
        if ent.health < 1:
            return False

        if not ent.isPlayer():
            # Only for players.
            return False

        didAnything = False

        if ent.inCondition(ent.CondBurning):
            ent.removeCondition(ent.CondBurning)
            didAnything = True

        if ent.takeHealth(max(1, ent.maxHealth // self.HealthRatio), 0):
            didAnything = True

        if didAnything:
            ent.emitSound("HealthKit.Touch", client=ent.owner)

        return didAnything

class DHealthKitSmallAI(DHealthKitAI):
    HealthRatio = 5
    ModelIndex = 5

class DHealthKitMediumAI(DHealthKitAI):
    HealthRatio = 2
    ModelIndex = 4

class DHealthKitFullAI(DHealthKitAI):
    HealthRatio = 1
    ModelIndex = 3

"""DAmmoPackAI module: contains the DAmmoPackAI class."""

from .DPickupItemBase import DPickupItemBaseAI

class DAmmoPackAI(DPickupItemBaseAI):

    def giveItem(self, ent):
        if ent.health < 1:
            return False

        from tf.player.DistributedTFPlayerAI import DistributedTFPlayerAI
        if not isinstance(ent, DistributedTFPlayerAI):
            # Only for players.
            return False

        gaveAny = False

        # Give ammo.
        for wpn in ent.weapons:
            wpn = base.air.doId2do.get(wpn)
            if not wpn:
                continue
            if not wpn.usesAmmo or wpn.ammo >= wpn.maxAmmo:
                continue
            maxToGive = max(0, wpn.maxAmmo - wpn.ammo)
            wpn.ammo += min(maxToGive, max(1, wpn.maxAmmo // self.AmmoRatio))

            if maxToGive > 0:
                gaveAny = True

        if gaveAny:
            ent.emitSound("AmmoPack.Touch", client=ent.owner)

        return gaveAny

class DAmmoPackSmallAI(DAmmoPackAI):
    AmmoRatio = 4
    ModelIndex = 2

class DAmmoPackMediumAI(DAmmoPackAI):
    AmmoRatio = 2
    ModelIndex = 1

class DAmmoPackFullAI(DAmmoPackAI):
    AmmoRatio = 1
    ModelIndex = 0

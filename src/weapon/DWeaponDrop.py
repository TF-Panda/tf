if not IS_CLIENT:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI
else:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar

from panda3d.core import CallbackObject, NodePath
from panda3d.pphysics import PhysTriggerCallbackData

from tf.tfbase.TFGlobals import SolidShape, SolidFlag
from tf.tfbase import CollisionGroups

class DWeaponDrop(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        self.packType = "med"
        self.metalAmount = 100
        self.singleUse = False
        self.lifetime = 60
        self.activeTime = 0.0
        if not IS_CLIENT:
            self.enabled = False
            self.triggerCallback = True
            self.sleepCallback = True
            self.solidShape = SolidShape.Box
            self.solidFlags = SolidFlag.Trigger
            self.fromCollideMask = CollisionGroups.Debris
            self.intoCollideMask = CollisionGroups.World
            self.useSeparateTriggerMask = True
            self.triggerIntoMask = CollisionGroups.Mask_Player
            self.used = False

    if not IS_CLIENT:
        def announceGenerate(self):
            BaseClass.announceGenerate(self)
            self.enabled = True
            self.activeTime = globalClock.frame_time

        def simulate(self):
            BaseClass.simulate(self)

            now = globalClock.frame_time
            if self.singleUse and self.enabled and ((now - self.activeTime) >= self.lifetime):
                base.net.deleteObject(self)

        #def onSleep(self):
        #    self.enabled = True
        #    self.activeTime = globalClock.frame_time

        #def onWake(self):
        #    self.enabled = False

        def onTriggerEnter(self, ent):
            if not self.enabled or self.used:
                return

            if ent.health <= 0:
                return

            if ent.__class__.__name__ == 'DistributedTFPlayerAI':
                gaveAny = False

                # Give ammo.
                for wpn in ent.weapons:
                    wpn = base.net.doId2do.get(wpn)
                    if not wpn:
                        continue
                    if not wpn.usesAmmo or wpn.ammo >= wpn.maxAmmo:
                        continue
                    maxToGive = max(0, wpn.maxAmmo - wpn.ammo)
                    if self.packType == "small":
                        wpn.ammo += min(maxToGive, max(1, wpn.maxAmmo // 4))
                    elif self.packType == "med":
                        # Fill half way at max.
                        wpn.ammo += min(maxToGive, max(1, wpn.maxAmmo // 2))
                    elif self.packType == "full":
                        wpn.ammo += maxToGive

                    if maxToGive > 0:
                        gaveAny = True

                if ent.usesMetal() and self.metalAmount > 0:
                    # Class can utilize metal.
                    maxToGive = max(0, ent.maxMetal - ent.metal)
                    ent.metal += min(maxToGive, self.metalAmount)
                    if maxToGive > 0:
                        gaveAny = True

                if gaveAny:
                    ent.emitSound("BaseCombatCharacter.AmmoPickup", client=ent.owner)
                    if self.singleUse:
                        self.enabled = False
                        self.used = True
                        base.net.deleteObject(self)

if not IS_CLIENT:
    DWeaponDropAI = DWeaponDrop
    DWeaponDropAI.__name__ = 'DWeaponDropAI'

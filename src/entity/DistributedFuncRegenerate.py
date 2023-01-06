"""DistributedFuncRegenerate module: contains the DistributedFuncRegenerate class."""

from .DistributedSolidEntity import DistributedSolidEntity

from tf.tfbase.TFGlobals import SolidShape, SolidFlag, TFTeam, WorldParent
from tf.tfbase import CollisionGroups

class DistributedFuncRegenerate(DistributedSolidEntity):
    """
    Implements resupply locker.  A trigger zone that regenerates player
    health and ammo every 3 seconds.  Linked to a model to play animations.
    """

    def __init__(self):
        DistributedSolidEntity.__init__(self)
        self.physType = self.PTConvex
        self.solidShape = SolidShape.Model
        self.solidFlags = SolidFlag.Trigger
        self.triggerCallback = True
        self.parentEntityId = WorldParent.Hidden

        if not IS_CLIENT:
            self.regenInterval = 3.0
            self.lastRegenTimes = {}
            self.touching = []
            self.modelTargetName = ""
            self.associatedModel = None
            self.isOpen = False
            self.closeTime = 0.0

    if not IS_CLIENT:

        def getAssociatedModel(self):
            if self.associatedModel:
                return self.associatedModel

            if self.modelTargetName:
                self.associatedModel = base.entMgr.findExactEntity(self.modelTargetName)

            return self.associatedModel

        def announceGenerate(self):
            DistributedSolidEntity.announceGenerate(self)

            self.initializeCollisions()
            self.addTask(self.__update, "updateFuncRegenerate", appendTask=True)

        def delete(self):
            self.associatedModel = None
            self.touching = None
            self.lastRegenTimes = None
            DistributedSolidEntity.delete(self)

        def initFromLevel(self, ent, properties):
            DistributedSolidEntity.initFromLevel(self, ent, properties)

            if properties.hasAttribute("associatedmodel"):
                self.modelTargetName = properties.getAttributeValue("associatedmodel").getString()

            # We accept a touch by any player because during a round end
            # the other team is allowed to use it.  We filter out enemies
            # in the trigger callback during the normal round.
            self.setIntoCollideMask(CollisionGroups.Mask_Player)

        def onTriggerEnter(self, entity):
            if not entity.isPlayer():
                return
            if not entity in self.touching:
                self.touching.append(entity)

        def onTriggerExit(self, entity):
            if not entity.isPlayer():
                return
            if entity in self.touching:
                self.touching.remove(entity)

        def doAnimTrack(self):
            if self.isOpen:
                self.closeTime += 2.0
            else:
                mdl = self.getAssociatedModel()
                if mdl:
                    mdl.setAnimation("open")
                self.closeTime = globalClock.frame_time + 2.0
                self.isOpen = True

        def regenPlayer(self, player):
            # Refill health, metal, and ammo for all weapons.
            player.health = max(player.health, player.maxHealth) # In case overhealed.
            player.metal = player.maxMetal
            for wpn in player.weapons:
                wpn = base.air.doId2do.get(wpn)
                if not wpn:
                    continue
                if wpn.usesAmmo:
                    wpn.ammo = wpn.maxAmmo
                if wpn.usesClip:
                    wpn.clip = wpn.maxClip
                if wpn.usesAmmo2:
                    wpn.ammo2 = wpn.maxAmmo2
                if wpn.usesClip:
                    wpn.clip2 = wpn.maxClip2
            if player.inCondition(player.CondBurning):
                player.removeCondition(player.CondBurning)

            self.doAnimTrack()

            # Play regen sound for this player only.
            self.emitSound("Regenerate.Touch", client=player.owner)

        def __update(self, task):
            now = globalClock.frame_time

            mdl = self.getAssociatedModel()
            if self.isOpen and mdl and now >= self.closeTime:
                mdl.setAnimation("close")
                self.isOpen = False

            if base.game.isStalemate():
                # Nobody can use it in a stalemate.
                return task.cont

            for entity in list(self.touching):
                if entity.isDODeleted():
                    self.touching.remove(entity)
                    continue

                if entity.isDead():
                    continue

                # If the round is over and non-stalemate, only the
                # winning team can use the locker.
                if base.game.isRoundEnded():
                    if entity.team != base.game.winTeam:
                        continue
                elif entity.team != self.team:
                    continue

                lastRegenTime = self.lastRegenTimes.get(entity.doId, 0.0)
                if (now - lastRegenTime) >= self.regenInterval:
                    self.regenPlayer(entity)
                    self.lastRegenTimes[entity.doId] = now

            return task.cont

if not IS_CLIENT:
    DistributedFuncRegenerateAI = DistributedFuncRegenerate
    DistributedFuncRegenerateAI.__name__ = 'DistributedFuncRegenerateAI'

"""DPickupItemBase module: contains the DPickupItemBase class."""

from panda3d.core import Vec3

from tf.entity.DistributedEntity import DistributedEntity
from tf.tfbase import TFGlobals

from direct.interval.IntervalGlobal import LerpHprInterval

class DPickupItemBase(DistributedEntity):
    """
    This is a base class for items that can be picked up by players for
    health and ammo (or potentially other things).

    Pickup items can have these behaviors:
    - Single use, item can be picked up once, deleted after.
    - Multi use, item will eventually regenerate after being picked up
    - Limited life, item will only be available for X number of seconds and
      will be deleted if no one picked it up, can only be picked up once.
    """

    def __init__(self):
        DistributedEntity.__init__(self)

        self.hidden = 0

        if not IS_CLIENT:
            self.modelIndex = self.ModelIndex
            # If true, the item can only be picked up once and the item
            # is deleted when picked up.  Otherwise, the item will regenerate
            # at a specified interval.
            self.singleUse = False
            # If single use, optionally the amount of time that the item will
            # be available before being deleted.
            self.lifetime = -1
            # If not single use, the amount of time in seconds after being
            # picked up that the item should become available again.
            self.regenInterval = 10.0

            # When we're disabled, we keep track of the first person to touch
            # us, so when we regenerate and that person is still touching us,
            # we can give the item to them right away.
            self.currentlyTouching = []

            self.enabled = False
            self.triggerCallback = True
            self.solidShape = TFGlobals.SolidShape.Box
            self.solidFlags = TFGlobals.SolidFlag.Trigger
            self.solidMask = TFGlobals.Contents.Solid | TFGlobals.Contents.AnyTeam
            self.collisionGroup = TFGlobals.CollisionGroup.Debris
            # All pickups use the same hull.
            self.hullMins = Vec3(-8)
            self.hullMaxs = Vec3(8)
        else:
            self.models = [
                "models/items/ammopack_large",
                "models/items/ammopack_medium",
                "models/items/ammopack_small",
                "models/items/medkit_large",
                "models/items/medkit_medium",
                "models/items/medkit_small"
            ]
            self.modelIndex = -1
            self.model = None
            self.spinIval = None

    if not IS_CLIENT:
        def generate(self):
            DistributedEntity.generate(self)
            self.initializeCollisions()
            if self.singleUse and self.lifetime > 0:
                self.addTask(self.__lifetimeTask, self.uniqueName('itemLifetime'), appendTask=True, delay=self.lifetime)
            self.enabled = True
            self.emitSoundSpatial("Item.Materialize")

        def giveItem(self, ent):
            """
            Intended to be overriden by derived classes to actually give the
            item to the indicated entity.

            Returns True if the item was actually given to the entity, false
            otherwise.
            """
            return False

        def onTriggerExit(self, ent):
            if ent in self.currentlyTouching:
                self.currentlyTouching.remove(ent)

        def onTriggerEnter(self, ent):
            """
            Called when an entity enters the trigger volume of this entity.
            """

            if not ent in self.currentlyTouching:
                self.currentlyTouching.append(ent)

            if not self.enabled:
                return

            if self.giveItem(ent):
                self.itemPickedUp()

        def itemPickedUp(self):
            self.enabled = False
            self.hidden = 1

            # If we're single use, delete ourselves right now.
            if self.singleUse:
                base.air.deleteObject(self)
            else:
                # Otherwise we need to disable ourselves and wait for the
                # respawn interval to come back.
                self.addTask(self.__regenTask, self.uniqueName('regenTask'), appendTask=True, delay=self.regenInterval)

        def __lifetimeTask(self, task):
            """
            When the item is single-use with a lifetime, this task removes the
            entity when the time is up.
            """
            base.air.deleteObject(self)
            return task.done

        def __regenTask(self, task):
            # It's time to regenerate!
            self.enabled = True
            self.hidden = 0
            # Play the extremely satisfying spawning sound.
            self.emitSoundSpatial("Item.Materialize")

            # If multiple players are touching the item at the time we
            # regenerate, give it to the first eligible player that started
            # touching the earliest.
            for ent in self.currentlyTouching:
                if self.giveItem(ent):
                    self.itemPickedUp()
                    break

            return task.done

        def delete(self):
            # Don't leak the entity that's touching us.
            self.currentlyTouching = None
            DistributedEntity.delete(self)

    else:
        def announceGenerate(self):
            DistributedEntity.announceGenerate(self)
            # Create an interval to spin the item.
            self.spinIval = LerpHprInterval(self.model, 3.0, (360, 0, 0), (0, 0, 0))
            self.spinIval.loop()

        def RecvProxy_hidden(self, hidden):
            if hidden != self.hidden:
                if hidden:
                    self.hide()
                else:
                    self.show()
                self.hidden = hidden

        def RecvProxy_modelIndex(self, index):
            if index != self.modelIndex:
                if self.model:
                    self.model.removeNode()
                self.model = base.loader.loadModel(self.models[index])
                self.model.reparentTo(self)
                self.modelIndex = index

        def disable(self):
            if self.spinIval:
                self.spinIval.finish()
                self.spinIval = None
            if self.model:
                self.model.removeNode()
                self.model = None
            DistributedEntity.disable(self)

if not IS_CLIENT:
    DPickupItemBaseAI = DPickupItemBase
    DPickupItemBaseAI.__name__ = 'DPickupItemBaseAI'

"""DPickupItemBase module: contains the DPickupItemBase class."""

from tf.entity.DistributedEntity import DistributedEntity

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

        self.models = [
            "models/items/ammopack_large",
            "models/items/ammopack_medium",
            "models/items/ammopack_small",
            "models/items/medkit_large",
            "models/items/medkit_medium",
            "models/items/medkit_small"
        ]

        self.modelIndex = 0

        if not IS_CLIENT:
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

            self.enabled = False
            self.triggerCallback = True
            self.solidShape = SolidShape.Box
            self.solidFlags = SolidFlag.Trigger
            self.solidMask = Contents.Solid | Contents.AnyTeam
            self.collisionGroup = CollisionGroup.Debris

    if not IS_CLIENT:
        def initializeCollisions(self):
            # Calculate the bounding box of the entity and use that as the
            # trigger volume for the item.
            self.calcTightBounds(self.hullMins, self.hullMaxs, self)
            DistributedEntity.initializeCollision(self)


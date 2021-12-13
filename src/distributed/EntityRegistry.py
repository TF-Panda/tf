"""EntityRegistry module: contains the EntityRegistry class."""

from direct.showbase.DirectObject import DirectObject


"""
This module contains a mapping of level entity classnames to Python classes,
similar to how the DC file maps dclasses to Python classes.  When a level
is loaded, it will use this registry to instantiate Python implementations
of entities found in the level.  The entities are expected to be
distributed objects (and probably inherit from `DistributedEntity`).  When a
Python level entity is instantiated, it will call `initFromLevel()` on the
object (before `generate()`), passing in the `PDXElement` of entity properties
specified in the level file.
"""

from .DHealthKitAI import DHealthKitSmallAI, DHealthKitMediumAI, DHealthKitFullAI
from .DAmmoPackAI import DAmmoPackSmallAI, DAmmoPackMediumAI, DAmmoPackFullAI

EntityRegistry = {
    "item_healthkit_small": DHealthKitSmallAI,
    "item_healthkit_medium": DHealthKitMediumAI,
    "item_healthkit_full": DHealthKitFullAI,
    "item_ammopack_small": DAmmoPackSmallAI,
    "item_ammopack_medium": DAmmoPackMediumAI,
    "item_ammopack_full": DAmmoPackFullAI
}

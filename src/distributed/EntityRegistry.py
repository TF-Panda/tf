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

from .World import WorldAI
from .DHealthKitAI import DHealthKitSmallAI, DHealthKitMediumAI, DHealthKitFullAI
from .DAmmoPackAI import DAmmoPackSmallAI, DAmmoPackMediumAI, DAmmoPackFullAI
from .DistributedTeamFlag import DistributedTeamFlagAI
from tf.entity.DistributedTrigger import DistributedTriggerAI
from tf.entity.DistributedFuncRegenerate import DistributedFuncRegenerateAI
from tf.entity.DistributedPropDynamic import DistributedPropDynamicAI
from tf.entity.DistributedFuncDoor import DistributedFuncDoorAI
from tf.entity.DistributedFuncBrush import DistributedFuncBrushAI
from tf.entity.DistributedPointSpotlight import DistributedPointSpotlightAI
from tf.entity.DistributedTriggerHurt import DistributedTriggerHurtAI
from tf.entity.TFEntityFilters import FilterActivatorTFTeam

EntityRegistry = {
    "worldspawn": WorldAI,
    "trigger_once": DistributedTriggerAI,
    "trigger_multiple": DistributedTriggerAI,
    "func_regenerate": DistributedFuncRegenerateAI,
    "prop_dynamic": DistributedPropDynamicAI,
    "func_door": DistributedFuncDoorAI,
    "func_brush": DistributedFuncBrushAI,
    "point_spotlight": DistributedPointSpotlightAI,
    "item_healthkit_small": DHealthKitSmallAI,
    "item_healthkit_medium": DHealthKitMediumAI,
    "item_healthkit_full": DHealthKitFullAI,
    "item_ammopack_small": DAmmoPackSmallAI,
    "item_ammopack_medium": DAmmoPackMediumAI,
    "item_ammopack_full": DAmmoPackFullAI,
    "item_teamflag": DistributedTeamFlagAI,
    "trigger_hurt": DistributedTriggerHurtAI,
    "filter_activator_tfteam": FilterActivatorTFTeam
}

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
from .DistributedTeamFlagAI import DistributedTeamFlagAI
from .DistributedTrigger import DistributedTriggerAI
from .DistributedFuncRegenerate import DistributedFuncRegenerateAI
from .DistributedPropDynamic import DistributedPropDynamicAI
from .DistributedFuncDoor import DistributedFuncDoorAI
from .DistributedFuncBrush import DistributedFuncBrushAI
from .DistributedPointSpotlight import DistributedPointSpotlightAI
from .DistributedTriggerHurt import DistributedTriggerHurtAI
from .DistributedFuncRotating import DistributedFuncRotatingAI
from .TFEntityFilters import FilterActivatorTFTeam
from .Ropes import RopeKeyFrameAI
from .TFLogicArena import TFLogicArena
from .TriggerCaptureAreaAI import TriggerCaptureAreaAI
from .TeamControlPoint import TeamControlPointAI
from .LogicRelay import LogicRelay
from .TeamRoundTimerAI import TeamRoundTimerAI
from .InfoPlayerTeamspawn import InfoPlayerTeamspawn
from .GameRoundWin import GameRoundWin
from .TeamControlPointMasterAI import TeamControlPointMasterAI
from .TeamControlPointRoundAI import TeamControlPointRoundAI
from .LogicAutoAI import LogicAutoAI
from .TFGameRulesProxyAI import TFGameRulesProxyAI

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
    "filter_activator_tfteam": FilterActivatorTFTeam,
    "func_rotating": DistributedFuncRotatingAI,
    "keyframe_rope": RopeKeyFrameAI,
    "move_rope": RopeKeyFrameAI,
    "tf_logic_arena": TFLogicArena,
    "trigger_capture_area": TriggerCaptureAreaAI,
    "team_control_point": TeamControlPointAI,
    "logic_relay": LogicRelay,
    "team_round_timer": TeamRoundTimerAI,
    "info_player_teamspawn": InfoPlayerTeamspawn,
    "game_round_win": GameRoundWin,
    "team_control_point_master": TeamControlPointMasterAI,
    "team_control_point_round": TeamControlPointRoundAI,
    "logic_auto": LogicAutoAI,
    "tf_gamerules": TFGameRulesProxyAI
}

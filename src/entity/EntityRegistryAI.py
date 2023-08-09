"""EntityRegistry module: contains the EntityRegistry class."""

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

from tf.object.DistributedDispenser import DistributedDispenserAI
from tf.object.DistributedTeleporter import (DistributedTeleporterEntranceAI,
                                             DistributedTeleporterExitAI)
from tf.object.SentryGun import SentryGunAI

from .DAmmoPackAI import DAmmoPackFullAI, DAmmoPackMediumAI, DAmmoPackSmallAI
from .DHealthKitAI import (DHealthKitFullAI, DHealthKitMediumAI,
                           DHealthKitSmallAI)
from .DistributedFuncBrush import DistributedFuncBrushAI
from .DistributedFuncDoor import DistributedFuncDoorAI
from .DistributedFuncRegenerate import DistributedFuncRegenerateAI
from .DistributedFuncRespawnRoomAI import DistributedFuncRespawnRoomAI
from .DistributedFuncRotating import DistributedFuncRotatingAI
from .DistributedPointSpotlight import DistributedPointSpotlightAI
from .DistributedPropDynamic import DistributedPropDynamicAI
from .DistributedTeamFlagAI import DistributedTeamFlagAI
from .DistributedTrigger import DistributedTriggerAI
from .DistributedTriggerHurt import DistributedTriggerHurtAI
from .GameRoundWin import GameRoundWin
from .InfoPlayerTeamspawn import InfoPlayerTeamspawn
from .LogicAutoAI import LogicAutoAI
from .LogicRelay import LogicRelay
from .RopesAI import RopeKeyFrameAI
from .TeamControlPoint import TeamControlPointAI
from .TeamControlPointMasterAI import TeamControlPointMasterAI
from .TeamControlPointRoundAI import TeamControlPointRoundAI
from .TeamRoundTimerAI import TeamRoundTimerAI
from .TFEntityFilters import FilterActivatorTFTeam
from .TFGameRulesProxyAI import TFGameRulesProxyAI
from .TFLogicArena import TFLogicArena
from .TriggerCaptureAreaAI import TriggerCaptureAreaAI
from .World import WorldAI

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
    "tf_gamerules": TFGameRulesProxyAI,
    "tf_obj_sentrygun": SentryGunAI,
    "tf_obj_dispenser": DistributedDispenserAI,
    "tf_obj_teleporter_entrance": DistributedTeleporterEntranceAI,
    "tf_obj_teleporter_exit": DistributedTeleporterExitAI,
    "func_respawnroom": DistributedFuncRespawnRoomAI
}

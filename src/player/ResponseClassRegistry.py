"""ResponseClassRegistry module: contains the ResponseClassRegistry class."""

from tf.player.TFClass import Class

from . import (DemoResponses, EngineerResponses, HeavyResponses,
               MedicResponses, PyroResponses, ScoutResponses, SniperResponses,
               SoldierResponses, SpyResponses)

ResponseClasses = {
  Class.Engineer: EngineerResponses,
  Class.Soldier: SoldierResponses,
  Class.Scout: ScoutResponses,
  Class.Pyro: PyroResponses,
  Class.Demo: DemoResponses,
  Class.HWGuy: HeavyResponses,
  Class.Medic: MedicResponses,
  Class.Sniper: SniperResponses,
  Class.Spy: SpyResponses
}

def reload():
    import importlib
    for mod in ResponseClasses.values():
        importlib.reload(mod)

"""ResponseClassRegistry module: contains the ResponseClassRegistry class."""

from . import EngineerResponses
from . import SoldierResponses
from tf.player.TFClass import Class

ResponseClasses = {
  Class.Engineer: EngineerResponses,
  Class.Soldier: SoldierResponses
}

def reload():
    import importlib
    for mod in ResponseClasses.values():
        importlib.reload(mod)

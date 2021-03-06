from panda3d.core import ConfigVariableDouble

sv_maxspeed = ConfigVariableDouble("sv-maxspeed", 400)
sv_maxvelocity = ConfigVariableDouble("sv-maxvelocity", 3500)
sv_rollspeed = ConfigVariableDouble("sv-rollspeed", 200)
sv_rollangle = ConfigVariableDouble("sv-rollangle", 0)
sv_friction = ConfigVariableDouble("sv-friction", 4)
sv_bounce = ConfigVariableDouble("sv-bounce")
sv_stepsize = ConfigVariableDouble("sv-stepsize")
sv_accelerate = ConfigVariableDouble("sv-accelerate", 10)
sv_airaccelerate = ConfigVariableDouble("sv-airaccelerate", 10)
sv_wateraccelerate = ConfigVariableDouble("sv-wateraccelerate", 10)
sv_waterfriction = ConfigVariableDouble("sv-waterfriction")
sv_stopspeed = ConfigVariableDouble("sv-stopspeed", 100)
sv_gravity = ConfigVariableDouble("sv-gravity", 800)

GAMEMOVEMENT_DUCK_TIME = 1000
GAMEMOVEMENT_JUMP_TIME = 510
GAMEMOVEMENT_JUMP_HEIGHT = 72 # units
TIME_TO_UNDUCK = 0.2
TIME_TO_DUCK = 0.2
GAMEMOVEMENT_TIME_TO_UNDUCK = (TIME_TO_UNDUCK * 1000.0)
GAMEMOVEMENT_TIME_TO_UNDUCK_INV = (GAMEMOVEMENT_DUCK_TIME - GAMEMOVEMENT_TIME_TO_UNDUCK)


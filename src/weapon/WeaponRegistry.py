from tf.player.TFClass import Weapon

from .DShotgun import DShotgun
from .DShotgunSecondary import DShotgunSecondary
from .DPistol import DPistol
from .DWrench import DWrench
from .DRocketLauncher import DRocketLauncher
from .DShovel import DShovel
from .DBottle import DBottle
from .DMinigun import DMinigun

Weapons = {
  Weapon.Shotgun: DShotgun,
  Weapon.ShotgunSecondary: DShotgunSecondary,
  Weapon.Pistol: DPistol,
  Weapon.Wrench: DWrench,
  Weapon.RocketLauncher: DRocketLauncher,
  Weapon.Shovel: DShovel,
  Weapon.Bottle: DBottle,
  Weapon.Minigun: DMinigun
}

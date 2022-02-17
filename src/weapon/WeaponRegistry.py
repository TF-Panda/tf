from tf.player.TFClass import Weapon

from .DistributedShotgun import (
  DistributedShotgunEngineer, DistributedShotgunSoldier,
  DistributedShotgunHeavy, DistributedShotgunPyro,
  DistributedScattergunScout)

from .DistributedPistol import DistributedPistolEngineer, DistributedPistolScout

from .DistributedWrench import DistributedWrench
from .DistributedRocketLauncher import DistributedRocketLauncher
from .DistributedShovel import DistributedShovel
from .DistributedBottle import DistributedBottle
from .DMinigun import DMinigun
from .DistributedGrenadeLauncher import DistributedGrenadeLauncher
from .DistributedBat import DistributedBat
from .DistributedFists import DistributedFists
from .DistributedFireAxe import DistributedFireAxe

Weapons = {
  Weapon.ShotgunEngineer: DistributedShotgunEngineer,
  Weapon.ShotgunSoldier: DistributedShotgunSoldier,
  Weapon.ShotgunHeavy: DistributedShotgunHeavy,
  Weapon.ShotgunPyro: DistributedShotgunPyro,
  Weapon.PistolEngineer: DistributedPistolEngineer,
  Weapon.PistolScout: DistributedPistolScout,
  Weapon.Wrench: DistributedWrench,
  Weapon.RocketLauncher: DistributedRocketLauncher,
  Weapon.Shovel: DistributedShovel,
  Weapon.Bottle: DistributedBottle,
  Weapon.Minigun: DMinigun,
  Weapon.GrenadeLauncher: DistributedGrenadeLauncher,
  Weapon.Scattergun: DistributedScattergunScout,
  Weapon.Bat: DistributedBat,
  Weapon.Fists: DistributedFists,
  Weapon.FireAxe: DistributedFireAxe
}

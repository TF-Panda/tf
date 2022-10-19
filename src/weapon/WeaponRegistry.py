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
from .DistributedRevolver import DistributedRevolver
from .DistributedKnife import DistributedKnife
from .DistributedPDA import DistributedConstructionPDA, DistributedDestructionPDA
from .DistributedToolbox import DistributedToolbox
from .DistributedBoneSaw import DistributedBoneSaw
from .DistributedMedigun import DistributedMedigun
from .DistributedSMG import DistributedSMG
from .DistributedMachete import DistributedMachete
from .DistributedSniperRifle import DistributedSniperRifle

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
  Weapon.FireAxe: DistributedFireAxe,
  Weapon.Revolver: DistributedRevolver,
  Weapon.Knife: DistributedKnife,
  Weapon.ConstructionPDA: DistributedConstructionPDA,
  Weapon.DestructionPDA: DistributedDestructionPDA,
  Weapon.Toolbox: DistributedToolbox,
  Weapon.BoneSaw: DistributedBoneSaw,
  Weapon.MediGun: DistributedMedigun,
  Weapon.SMG: DistributedSMG,
  Weapon.Machete: DistributedMachete,
  Weapon.SniperRifle: DistributedSniperRifle
}

from tf.player.TFClass import Weapon

from .DistributedBat import DistributedBat
from .DistributedBoneSaw import DistributedBoneSaw
from .DistributedBottle import DistributedBottle
from .DistributedFireAxe import DistributedFireAxe
from .DistributedFists import DistributedFists
from .DistributedFlameThrower import DistributedFlameThrower
from .DistributedGrenadeLauncher import DistributedGrenadeLauncher
from .DistributedKnife import DistributedKnife
from .DistributedMachete import DistributedMachete
from .DistributedMedigun import DistributedMedigun
from .DistributedPDA import (DistributedConstructionPDA,
                             DistributedDestructionPDA)
from .DistributedPistol import (DistributedPistolEngineer,
                                DistributedPistolScout)
from .DistributedRevolver import DistributedRevolver
from .DistributedRocketLauncher import DistributedRocketLauncher
from .DistributedShotgun import (DistributedScattergunScout,
                                 DistributedShotgunEngineer,
                                 DistributedShotgunHeavy,
                                 DistributedShotgunPyro,
                                 DistributedShotgunSoldier)
from .DistributedShovel import DistributedShovel
from .DistributedSMG import DistributedSMG
from .DistributedSniperRifle import DistributedSniperRifle
from .DistributedStickyBombLauncher import DistributedStickyBombLauncher
from .DistributedToolbox import DistributedToolbox
from .DistributedWrench import DistributedWrench
from .DMinigun import DMinigun

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
  Weapon.SniperRifle: DistributedSniperRifle,
  Weapon.StickyBombLauncher: DistributedStickyBombLauncher,
  Weapon.FlameThrower: DistributedFlameThrower
}

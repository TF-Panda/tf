
from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase import CollisionGroups, TFFilters, TFGlobals, TFLocalizer

from .TFWeaponMelee import TFWeaponMelee
from .WeaponMode import TFWeaponMode, TFWeaponType

SWING_MINS = Vec3(-18)
SWING_MAXS = Vec3(18)

class DistributedWrench(TFWeaponMelee):

    WeaponModel = "models/weapons/c_wrench"
    WeaponViewModel = "models/weapons/v_wrench_engineer"
    UsesViewModel = True
    MinViewModelOffset = (10, -2, -9)

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.usesAmmo = False
        self.usesClip = False
        self.meleeWeapon = True
        self.reloadsSingly = False
        self.primaryAttackInterval = 1.0
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary]['damage'] = 65
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['smackDelay'] = 0.2

    #def onEntityHit(self, ent):
    #    if isinstance(ent, BaseObject) and ent.team == self.player.team:
    #        # Hit a friendly building.
    #        self.onFriendlyBuildingHit(ent)

    def onFriendlyBuildingHit(self, bldg):
        usefulHit = bldg.inputWrenchHit(self.player)
        if usefulHit:
            self.playSound("Weapon_Wrench.HitBuilding_Success", False)
        else:
            self.playSound("Weapon_Wrench.HitBuilding_Failure", False)

    def smack(self):
        # See if we can hit an object with a higher range.

        # Only trace against objects.
        filter = TFFilters.TFQueryFilter(self.player)

        contents = CollisionGroups.RedBuilding if self.team == TFGlobals.TFTeam.Red else CollisionGroups.BlueBuilding

        # Setup swing range
        q = Quat()
        q.setHpr(self.player.viewAngles)
        forward = q.getForward()
        swingStart = self.player.getEyePosition()
        swingEnd = swingStart + (forward * 70)

        tr = TFFilters.traceLine(swingStart, swingEnd, contents, filter)
        if not tr['hit']:
            tr = TFFilters.traceBox(swingStart, swingEnd, SWING_MINS, SWING_MAXS, contents, filter, self.player.viewAngles)

        ent = tr['ent']

        if ent and ent.isObject() and ent.team == self.player.team:
            if not IS_CLIENT:
                # Hit a friendly building.
                self.onFriendlyBuildingHit(ent)
        else:
            # Didn't hit a friendly building, smack as usual for player hits.
            TFWeaponMelee.smack(self)

    def getSingleSound(self):
        return "Weapon_Wrench.Miss"

    def getHitPlayerSound(self):
        return "Weapon_Wrench.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Wrench.HitWorld"

    def getName(self):
        return TFLocalizer.Wrench

if not IS_CLIENT:
    DistributedWrenchAI = DistributedWrench
    DistributedWrenchAI.__name__ = 'DistributedWrenchAI'

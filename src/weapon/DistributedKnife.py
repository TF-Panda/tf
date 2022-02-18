"""DistributedKnife module: contains the DistributedKnife class."""

from .TFWeaponMelee import TFWeaponMelee

from .WeaponMode import TFWeaponType, TFWeaponMode

from tf.tfbase import TFLocalizer
from tf.actor.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent

from panda3d.core import *

class DistributedKnife(TFWeaponMelee):

    WeaponModel = "models/weapons/w_knife"
    WeaponViewModel = "models/weapons/v_knife_spy"
    UsesViewModel = True

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.primaryAttackInterval = 0.8
        self.weaponData[TFWeaponMode.Primary]['damage'] = 40
        self.weaponData[TFWeaponMode.Primary]['timeFireDelay'] = 0.8
        self.weaponData[TFWeaponMode.Primary]['smackDelay'] = 0.1
        self.weaponData[TFWeaponMode.Primary]['timeIdle'] = 5.0
        self.weaponData[TFWeaponMode.Secondary]['smackDelay'] = 0.6

        self.backstabVictim = None

    def primaryAttack(self):
        #if not self.canAttack():
        #    return

        self.weaponMode = TFWeaponMode.Primary

        hadHit, result = self.doSwingTrace()
        if hadHit:
            # We will hit something with the attack.
            block = result.getBlock()
            np = NodePath(block.getActor())
            ent = np.getNetPythonTag("entity")
            if ent and ('TFPlayer' in ent.__class__.__name__):
                if ent.team != self.player.team:
                    # Deal extra damage to players when stabbing them from behind.
                    if self.isBehindTarget(ent):
                        self.weaponMode = TFWeaponMode.Secondary
                        self.backstabVictim = ent

        self.swing()

    #def itemPostFrame(self):
    #    TFWeaponMelee.itemPostFrame(self)
    #    if self.weaponMode == TFWeaponMode.Secondary:


    def doViewModelAnimation(self):
        if self.weaponMode == TFWeaponMode.Secondary:
            # Raise up.
            self.sendWeaponAnim(Activity.VM_Backstab_Up)
            # Then stab.
            self.setNextWeaponAnim(Activity.VM_Swing_Hard)
        else:
            self.sendWeaponAnim(Activity.VM_Fire)

    def doPlayerAnimation(self, player):
        if self.weaponMode == TFWeaponMode.Secondary:
            player.doAnimationEvent(PlayerAnimEvent.AttackSecondary)
        else:
            player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)

    def isBehindTarget(self, target):
        q = Quat()
        q.setHpr((target.eyeH * 360, target.eyeP * 360, 0.0))
        victimForward = q.getForward()
        victimForward.z = 0.0
        victimForward.normalize()

        # Get a vector from my origin to my target's origin.
        toTarget = target.getWorldSpaceCenter() - self.player.getWorldSpaceCenter()
        toTarget.z = 0.0
        toTarget.normalize()

        dot = victimForward.dot(toTarget)
        return dot > -0.1

    def getMeleeDamage(self, target):
        baseDamage = TFWeaponMelee.getMeleeDamage(self, target)

        if 'TFPlayer' in target.__class__.__name__:
            if self.isBehindTarget(target) or \
                (self.weaponMode == TFWeaponMode.Secondary and self.backstabVictim == target):

                baseDamage = target.health * 2

        return baseDamage

    def getSingleSound(self):
        return "Weapon_Knife.Miss"

    def getHitPlayerSound(self):
        return "Weapon_Knife.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Knife.HitWorld"

    def getName(self):
        return TFLocalizer.Knife

if not IS_CLIENT:
    DistributedKnifeAI = DistributedKnife
    DistributedKnifeAI.__name__ = 'DistributedKnifeAI'

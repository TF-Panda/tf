"""DistributedKnife module: contains the DistributedKnife class."""

from panda3d.core import *

from tf.actor.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.tfbase import TFLocalizer

from .TFWeaponMelee import TFWeaponMelee
from .WeaponMode import TFWeaponMode, TFWeaponType


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
        self.weaponData[TFWeaponMode.Secondary]['smackDelay'] = 0.2
        self.weaponData[TFWeaponMode.Secondary]['damage'] = 40
        self.weaponReset()

    def weaponReset(self):
        self.blockedTime = -1
        self.backstabVictim = None
        self.readyToBackstab = False

    if IS_CLIENT:
        def addPredictionFields(self):
            TFWeaponMelee.addPredictionFields(self)
            self.addPredictionField("readyToBackstab", int, networked=True)

    def deactivate(self):
        self.weaponReset()
        TFWeaponMelee.deactivate(self)

    def isBackstab(self):
        return self.backstabVictim is not None

    def primaryAttack(self):
        #if not self.canAttack():
        #    return

        self.weaponMode = TFWeaponMode.Primary
        self.backstabVictim = None

        tr = self.doSwingTrace()
        if tr['hit']:
            # We will hit something with the attack.
            ent = tr['ent']
            if ent and ent.isPlayer() and not ent.isDead() and ent.team != self.player.team:
                # Deal extra damage to players when stabbing them from behind.
                if self.canPerformBackstabAgainstTarget(ent):
                    # Store the victim to compare when we do the damage.
                    self.backstabVictim = ent

        # Swing the weapon.
        self.swing()
        self.smack()
        self.smackTime = -1

        # Hand is down.
        self.readyToBackstab = False

    def itemPostFrame(self):
        if not IS_CLIENT:
            # Move other players back to history positions based on local player's lag.
            base.air.lagComp.startLagCompensation(self.player, self.player.currentCommand)

        self.syncAllHitBoxes()

        self.backstabVMThink()
        TFWeaponMelee.itemPostFrame(self)

        if not IS_CLIENT:
            base.air.lagComp.finishLagCompensation(self.player)

    def backstabVMThink(self):
        act = self.activity
        if act not in (Activity.VM_Idle, Activity.VM_Backstab_Idle):
            return

        # Are we in backstab range and not cloaked?
        tr = self.doSwingTrace()
        if tr['hit']:
            ent = tr['ent']
            if ent and ent.isPlayer() and ent.team != self.player.team:
                if self.canPerformBackstabAgainstTarget(ent):
                    if not self.readyToBackstab:
                        self.sendWeaponAnim(Activity.VM_Backstab_Up)
                        self.readyToBackstab = True
                elif self.readyToBackstab:
                    self.sendWeaponAnim(Activity.VM_Backstab_Down)
                    self.readyToBackstab = False
        else:
            if self.readyToBackstab:
                self.sendWeaponAnim(Activity.VM_Backstab_Down)
                self.readyToBackstab = False

    def sendWeaponAnim(self, act):
        if self.readyToBackstab:
            if act == Activity.VM_Idle:
                act = Activity.VM_Backstab_Idle
            elif act == Activity.VM_Fire:
                act = Activity.VM_Swing_Hard

        TFWeaponMelee.sendWeaponAnim(self, act)

    def doPlayerAnimation(self, player):
        if self.isBackstab():
            player.doAnimationEvent(PlayerAnimEvent.AttackSecondary)
        else:
            player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)

    def canPerformBackstabAgainstTarget(self, target):
        if not target:
            return False

        if self.isBehindAndFacingTarget(target):
            return True

        return False

    def isBehindAndFacingTarget(self, target):
        # Get a vector from my origin to my target's origin.
        toTarget = target.getWorldSpaceCenter() - self.player.getWorldSpaceCenter()
        toTarget.z = 0.0
        toTarget.normalize()

        # Get owner forward view vector.
        q = Quat()
        q.setHpr(self.player.viewAngles)
        ownerForward = q.getForward()
        ownerForward.z = 0.0
        ownerForward.normalize()

        # Get target forward view vector
        q.setHpr((target.eyeH * 360, target.eyeP * 360, 0.0))
        targetForward = q.getForward()
        targetForward.z = 0.0
        targetForward.normalize()

        # Make sure owner is behind, facing and aiming at target's back.
        posVsTargetViewDot = toTarget.dot(targetForward) # Behind?
        posVsOwnerViewDot = toTarget.dot(ownerForward) # Facing?
        viewAnglesDot = targetForward.dot(ownerForward)

        return posVsTargetViewDot > 0 and posVsOwnerViewDot > 0.5 and viewAnglesDot > -0.3

    def getMeleeDamage(self, target):
        baseDamage = TFWeaponMelee.getMeleeDamage(self, target)

        self.currentAttackIsCritical = False
        if target.isPlayer():
            if self.isBackstab():
                # Do twice the target's health so that random modification will still
                # kill him.
                baseDamage = target.health * 2
                self.currentAttackIsCritical = True

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

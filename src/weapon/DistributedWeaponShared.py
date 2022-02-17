"""DistributedWeaponShared module: contains the DistributedWeaponShared class"""

from tf.actor.Char import Char

from tf.actor.Activity import Activity
from tf.player.InputButtons import InputFlag
from tf.tfbase.TFGlobals import CollisionGroup, Contents

from panda3d.pphysics import *
from panda3d.core import *

class DistributedWeaponShared:
    """
    Base weapon logic shared between client and server for prediction.
    """

    WeaponModel = None
    WeaponViewModel = None
    UsesViewModel = False
    HideWeapon = False

    def __init__(self):
        self.ammo = 0
        self.ammo2 = 0
        self.maxAmmo = 0
        self.maxAmmo2 = 0
        self.clip = 0
        self.clip2 = 0
        self.maxClip = 0
        self.maxClip2 = 0
        self.playerId = -1
        # Player DO
        self.player = None
        # ViewModel DO
        self.viewModel = None

        self.viewModelChar = None

        # Do we use a clip at all?  Would be true for the pistol, shotgun, etc,
        # false for the minigun.
        self.usesClip = True
        self.usesClip2 = False

        # If true, increments the clip one by one when reloading, otherwise the
        # entire clip is refilled at once when reloading.
        self.reloadsSingly = False

        # Do we use ammo at all?  Would be false for things like melee weapons.
        self.usesAmmo = True
        self.usesAmmo2 = False

        # When are we allowed to primary attack next?
        self.nextPrimaryAttack = 0.0
        self.nextSecondaryAttack = 0.0

        self.nextEmptySoundTime = 0.0

        # Currently reloading?
        self.inReload = False

        self.meleeWeapon = False

        self.fireDuration = 0.0

        self.timeWeaponIdle = 0.0

        self.lowered = False
        self.fireOnEmpty = False

        self.activity = Activity.Invalid
        self.idealActivity = Activity.Invalid
        self.idealSequence = -1
        self.sequence = -1
        self.primaryAttackInterval = 1.0
        self.actTable = {}
        self.vmActTable = {}

    def syncAllHitBoxes(self):
        # Make sure all characters have their hit boxes synchronized.
        for do in base.net.doId2do.values():
            if isinstance(do, Char):
                do.syncHitBoxes()

    def getVMSequenceLength(self):
        return self.viewModel.getDuration()

    def playSound(self, name):
        # Only the server (AI) implements this currently.
        pass

    def activate(self):
        assert self.player
        self.sendWeaponAnim(Activity.VM_Draw)
        self.nextPrimaryAttack = globalClock.getFrameTime() + self.viewModel.getDuration()
        self.nextSecondaryAttack = self.nextPrimaryAttack

    def deactivate(self):
        assert self.player

    def getName(self):
        return "weapon_name"

    def getSingleSound(self):
        return ""

    def getEmptySound(self):
        return ""

    def getHitPlayerSound(self):
        return "Weapon_Crowbar.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Crowbar.HitWorld"

    def getReloadSound(self):
        return ""

    def isWeaponVisible(self):
        return True

    def translateViewModelActivity(self, activity):
        return self.vmActTable.get(activity, activity)

    def translateActivity(self, activity):
        return self.actTable.get(activity, activity)

    def sendWeaponAnim(self, activity):
        activity = self.translateViewModelActivity(activity)
        # Just set the ideal activity and be done with it.
        return self.setIdealActivity(activity)

    def maintainIdealActivity(self):
        if self.activity != Activity.Transition:
            return

        if self.activity == self.idealActivity and self.sequence == self.idealSequence:
            return

        if (not self.viewModel.isCurrentChannelFinished()):
            return

        # Move to the next animation towards our ideal.
        self.sendWeaponAnim(self.idealActivity)

    def setIdealActivity(self, act):
        idealSequence = self.viewModel.getChannelForActivity(act)
        if idealSequence == -1:
            return False

        # Take the new activity
        self.idealActivity = act
        self.idealSequence = idealSequence

        nextSequence = self.idealSequence
        if act != Activity.VM_Draw and self.isWeaponVisible() and nextSequence != self.idealSequence:
            self.activity = Activity.Transition
            self.sequence = nextSequence
            self.sendViewModelAnim(nextSequence)
        else:
            self.activity = self.idealActivity
            self.sequence = self.idealSequence
            self.sendViewModelAnim(self.idealSequence)

        self.timeWeaponIdle = globalClock.getFrameTime() + self.viewModel.getDuration()
        return True

    def sendViewModelAnim(self, seq):
        if seq < 0:
            return

        if not self.viewModel:
            return

        self.viewModel.startChannel(seq)

    def weaponIdle(self):
        if self.hasWeaponIdleTimeElapsed():
            self.sendWeaponAnim(Activity.VM_Idle)
            self.timeWeaponIdle = globalClock.getFrameTime() + self.viewModel.getDuration()

    def hasWeaponIdleTimeElapsed(self):
        if globalClock.getFrameTime() > self.timeWeaponIdle:
            return True
        return False

    def reloadOrSwitchWeapons(self):
        """
        If the current weapon has more ammo, reload it.  Otherwise, switch
        to the next best weapon we've got.  Returns true if it took any action.
        """
        assert self.player

        self.fireOnEmpty = False

        # If we don't have any ammo, switch to the next best weapon.
        if not self.hasAnyAmmo() and self.nextPrimaryAttack < globalClock.getFrameTime() and self.nextSecondaryAttack < globalClock.getFrameTime():
            # Weapon isn't useable, switch.
            switched = False
            # Cycle through all the weapons starting at the weapon next to this
            # one and pick the first weapon we can switch to.
            index = (self.player.activeWeapon + 1) % len(self.player.weapons)
            while index != self.player.activeWeapon:
                wpnId = self.player.weapons[index]
                if wpnId == self.doId:
                    continue
                wpn = base.net.doId2do.get(wpnId)
                assert wpn
                if wpn.hasAnyAmmo():
                    # Switch to this one.
                    self.player.setActiveWeapon(index)
                    switched = True
                    break
                index = (index + 1) % len(self.player.weapons)
            if switched:
                self.nextPrimaryAttack = globalClock.getFrameTime() + 0.3
                return True
        else:
            # Weapon is useable.  Reload is empty and weapon has waited as long as it has to after firing.
            if self.usesClip and (self.clip == 0) and self.nextPrimaryAttack < globalClock.getFrameTime() and self.nextSecondaryAttack < globalClock.getFrameTime():
                # If we're successfully reloading, we're done.
                if self.reload():
                    return True

        return False

    def hasAnyAmmo(self):
        # If I don't use ammo of any kind, I can always fire.
        if not self.usesAmmo and not self.usesAmmo2:
            return True

        # Otherwise, I need ammo of either type.
        return self.hasAmmo() or self.hasAmmo2()

    def hasAmmo(self):
        if self.usesClip:
            if self.clip > 0:
                return True

        # Otherwise, I have ammo if I have some in my ammo counts.
        if self.ammo > 0:
            return True

        return False

    def hasAmmo2(self):
        if self.usesClip2:
            if self.clip2 > 0:
                return True

        # Otherwise, I have ammo if I have some in my ammo counts.
        if self.ammo2 > 0:
            return True

        return False

    def checkReload(self):
        if self.reloadsSingly:
            if not self.player:
                return

            if self.inReload and self.nextPrimaryAttack <= globalClock.getFrameTime():
                if (self.player.buttons & (InputFlag.Attack1 | InputFlag.Attack2)) and self.clip > 0:
                    # We loaded in at least one shell and we want to fire.  Stop reloading.
                    self.inReload = False
                    return

                if self.ammo <= 0:
                    # No more ammo, end reload.
                    self.finishReload()
                    return
                elif self.clip < self.maxClip:
                    # Add them to the clip.
                    self.clip += 1
                    self.ammo -= 1
                    self.reload()
                    return
                else:
                    # Clip full, stop reloading.
                    self.finishReload()
                    self.nextPrimaryAttack = globalClock.getFrameTime()
                    self.nextSecondaryAttack = globalClock.getFrameTime()
                    return
        else:
            if self.inReload and self.nextPrimaryAttack <= globalClock.getFrameTime():
                self.finishReload()
                self.nextPrimaryAttack = globalClock.getFrameTime()
                self.nextSecondaryAttack = globalClock.getFrameTime()
                self.inReload = False

    def finishReload(self):
        if not self.player:
            return

        if self.usesClip:
            primary = min(self.maxClip - self.clip, self.ammo)
            self.clip += primary
            self.ammo -= primary

        # TODO: clips for ammo2

        if self.reloadsSingly:
            self.inReload = False

    def reload(self):
        return self.defaultReload(self.maxClip, Activity.VM_Reload)

    def defaultReload(self, clipSize1, activity):
        if not self.player:
            return False

        # If I don't have any spare ammo, I can't reload
        if self.ammo <= 0:
            return False

        reload = False

        # If you don't have clips, then don't try to reload them.
        if self.usesClip:
            # Need to reload clip?
            primary = min(clipSize1 - self.clip, self.ammo)
            if primary != 0:
                reload = True

        # TODO: self.usesClip2

        if not reload:
            return False

        # TODO: reload sound
        self.sendWeaponAnim(activity)
        #self.setPlayerGesture(playerActivity)

        sequenceEndTime = globalClock.getFrameTime() + self.viewModel.getDuration()
        self.nextPrimaryAttack = self.nextSecondaryAttack = sequenceEndTime

        self.inReload = True

        return True

    def handleFireOnEmpty(self):
        if self.fireOnEmpty:
            self.reloadOrSwitchWeapons()
            self.fireDuration = 0.0
        else:
            if self.nextEmptySoundTime < globalClock.getFrameTime():
                self.playSound(self.getEmptySound())
                self.nextEmptySoundTime = globalClock.getFrameTime() + 0.5
            self.fireOnEmpty = False

    def primaryAttack(self):
        self.sendWeaponAnim(Activity.VM_Fire)
        #self.setPlayerGesture(Activity.Primary_Stand_Attack)
        self.nextPrimaryAttack = globalClock.getFrameTime() + self.primaryAttackInterval
        if self.usesClip:
            self.clip -= 1

        self.playSound(self.getSingleSound())

        self.syncAllHitBoxes()

    def itemPreFrame(self):
        #if self.viewModel.isCurrentSequenceFinished():
        #    self.selectNextActivity(self.activity)
        self.maintainIdealActivity()

    def itemBusyFrame(self):
        pass

    def itemPostFrame(self):
        if not self.player:
            return

        # Track the duration of the fire.
        self.fireDuration = (self.fireDuration + globalClock.getFrameTime()) if (self.player.buttons & InputFlag.Attack2) else 0.0

        if self.usesClip:
            self.checkReload()

        fired = False

        # Secondary attack has priority
        if (self.player.buttons & InputFlag.Attack2) and (self.nextSecondaryAttack <= globalClock.getFrameTime()):
            if self.usesAmmo2 and self.ammo2 <= 0:
                if self.nextEmptySoundTime < globalClock.getFrameTime():
                    self.playSound(self.getEmptySound())
                    self.nextSecondaryAttack = self.nextEmptySoundTime = globalClock.getFrameTime() + 0.5
            else:
                fired = True
                self.secondaryAttack()
                if self.usesClip2:
                    # Reload clip2 if empty.
                    if self.clip2 < 1:
                        self.ammo2 -= 1
                        self.clip2 += 1

        if not fired and (self.player.buttons & InputFlag.Attack1) and globalClock.getFrameTime() > self.nextPrimaryAttack:
            # It's time to primary attack.

            if not self.meleeWeapon and (self.usesClip and self.clip <= 0) or ((not self.usesClip) and (self.usesAmmo and self.ammo <= 0)):
                # No clip or no ammo.
                self.handleFireOnEmpty()
            else:
                # TODO: if the firing button was just pressed, or the alt-fire just released, reset the firing time
                self.primaryAttack()

        # Reload pressed /clip empty
        if (self.player.buttons & InputFlag.Reload) and self.usesClip and not self.inReload:
            # Reload when reload is pressed, or if no buttons are down and weapon is empty.
            self.reload()
            self.fireDuration = 0.0

        # No buttons down.
        if not (self.player.buttons & (InputFlag.Attack1 | InputFlag.Attack2 | InputFlag.Reload)):
            # No fire buttons down or reloading.
            if (not self.reloadOrSwitchWeapons()) and not self.inReload:
                self.weaponIdle()

    def setPlayerId(self, playerId):
        self.playerId = playerId
        self.updatePlayer()

    def updatePlayer(self):
        if self.playerId != -1:
            self.player = base.net.doId2do.get(self.playerId)
            if self.player:
                self.viewModel = self.player.viewModel
            else:
                self.viewModel = None
        else:
            self.player = None
            self.viewModel = None

    def generate(self):
        if not self.UsesViewModel:
            self.viewModelChar = Char()
            self.viewModelChar.loadModel(self.WeaponViewModel)

    def delete(self):
        if self.viewModelChar:
            self.viewModelChar.clearModel()
            self.viewModelChar = None
        self.player = None
        self.viewModel = None

    def getAmmo(self):
        return self.ammo

    def getMaxAmmo(self):
        return self.maxAmmo

    def getClip(self):
        return self.clip

    def getMaxClip(self):
        return self.maxClip

from .DistributedWeaponAI import DistributedWeaponAI

from .WeaponMode import TFWeaponMode, TFReloadMode, TFWeaponType

from tf.character.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from .FireBullets import fireBullets

class TFWeaponAI(DistributedWeaponAI):

    def __init__(self):
        DistributedWeaponAI.__init__(self)
        self.weaponMode = TFWeaponMode.Primary
        self.reloadMode = TFReloadMode.Start
        self.inAttack = False
        self.inAttack2 = False
        self.currentAttackIsCrit = False
        self.lowered = False
        self.reloadStartClipAmount = 0
        self.critTime = 0.0
        self.lastCritCheckTime = 0.0
        self.lastCritCheckFrame = 0.0
        self.currentSeed = -1
        self.resetParity = False
        self.reloadedThroughAnimEvent = False
        self.weaponData = {}

        self.weaponType = TFWeaponType.Primary

        self.vmActTable = {
            TFWeaponType.Primary: {
                Activity.VM_Draw: Activity.Primary_VM_Draw,
                Activity.VM_Idle: Activity.Primary_VM_Idle,
                Activity.VM_Fire: Activity.Primary_VM_Fire,
                Activity.VM_Reload: Activity.Primary_VM_Reload,
                Activity.VM_Reload_Start: Activity.Primary_VM_Reload_Start,
                Activity.VM_Reload_Finish: Activity.Primary_VM_Reload_End
            },

            TFWeaponType.Secondary: {
                Activity.VM_Draw: Activity.Secondary_VM_Draw,
                Activity.VM_Idle: Activity.Secondary_VM_Idle,
                Activity.VM_Fire: Activity.Secondary_VM_Fire,
                Activity.VM_Reload: Activity.Secondary_VM_Reload,
                Activity.VM_Reload_Start: Activity.Secondary_VM_Reload_Start,
                Activity.VM_Reload_Finish: Activity.Secondary_VM_Reload_End
            },

            TFWeaponType.Melee: {
                Activity.VM_Draw: Activity.Melee_VM_Draw,
                Activity.VM_Idle: Activity.Melee_VM_Idle,
                Activity.VM_Fire: Activity.Melee_VM_Swing
            }
        }

        self.actTable = {
            TFWeaponType.Primary: {
                Activity.Stand: Activity.Primary_Stand,
                Activity.Run: Activity.Primary_Run,
                Activity.Crouch: Activity.Primary_Crouch,
                Activity.Crouch_Walk: Activity.Primary_Crouch_Walk,
                Activity.Swim: Activity.Primary_Swim,
                Activity.Air_Walk: Activity.Primary_Air_Walk,
                Activity.Jump: Activity.Primary_Jump,
                Activity.Jump_Start: Activity.Primary_Jump_Start,
                Activity.Jump_Float: Activity.Primary_Jump_Float,
                Activity.Jump_Land: Activity.Primary_Jump_Land,
                Activity.Double_Jump_Crouch: Activity.Primary_Double_Jump_Crouch,
                Activity.Attack_Stand: Activity.Primary_Attack_Stand,
                Activity.Attack_Crouch: Activity.Primary_Attack_Crouch,
                Activity.Attack_Swim: Activity.Primary_Attack_Swim,
                Activity.Attack_Air_Walk: Activity.Primary_Attack_Air_Walk,
                Activity.Reload_Stand: Activity.Primary_Reload_Stand,
                Activity.Reload_Stand_Loop: Activity.Primary_Reload_Stand_Loop,
                Activity.Reload_Stand_End: Activity.Primary_Reload_Stand_End,
                Activity.Reload_Crouch: Activity.Primary_Reload_Crouch,
                Activity.Reload_Crouch_Loop: Activity.Primary_Reload_Crouch_Loop,
                Activity.Reload_Crouch_End: Activity.Primary_Reload_Crouch_End,
                Activity.Reload_Swim: Activity.Primary_Reload_Swim,
                Activity.Reload_Swim_Loop: Activity.Primary_Reload_Swim_Loop,
                Activity.Reload_Swim_End: Activity.Primary_Reload_Swim_End,
                Activity.Reload_Air_Walk: Activity.Primary_Reload_Air_Walk,
                Activity.Reload_Air_Walk_Loop: Activity.Primary_Reload_Air_Walk_Loop,
                Activity.Reload_Air_Walk_End: Activity.Primary_Reload_Air_Walk_End
            },

            TFWeaponType.Secondary: {
                Activity.Stand: Activity.Secondary_Stand,
                Activity.Run: Activity.Secondary_Run,
                Activity.Crouch: Activity.Secondary_Crouch,
                Activity.Crouch_Walk: Activity.Secondary_Crouch_Walk,
                Activity.Swim: Activity.Secondary_Swim,
                Activity.Air_Walk: Activity.Secondary_Air_Walk,
                Activity.Jump: Activity.Secondary_Jump,
                Activity.Jump_Start: Activity.Secondary_Jump_Start,
                Activity.Jump_Float: Activity.Secondary_Jump_Float,
                Activity.Jump_Land: Activity.Secondary_Jump_Land,
                Activity.Double_Jump_Crouch: Activity.Secondary_Double_Jump_Crouch,
                Activity.Attack_Stand: Activity.Secondary_Attack_Stand,
                Activity.Attack_Crouch: Activity.Secondary_Attack_Crouch,
                Activity.Attack_Swim: Activity.Secondary_Attack_Swim,
                Activity.Attack_Air_Walk: Activity.Secondary_Attack_Air_Walk,
                Activity.Reload_Stand: Activity.Secondary_Reload_Stand,
                Activity.Reload_Stand_Loop: Activity.Secondary_Reload_Stand_Loop,
                Activity.Reload_Stand_End: Activity.Secondary_Reload_Stand_End,
                Activity.Reload_Crouch: Activity.Secondary_Reload_Crouch,
                Activity.Reload_Crouch_Loop: Activity.Secondary_Reload_Crouch_Loop,
                Activity.Reload_Crouch_End: Activity.Secondary_Reload_Crouch_End,
                Activity.Reload_Swim: Activity.Secondary_Reload_Swim,
                Activity.Reload_Swim_Loop: Activity.Secondary_Reload_Swim_Loop,
                Activity.Reload_Swim_End: Activity.Secondary_Reload_Swim_End,
                Activity.Reload_Air_Walk: Activity.Secondary_Reload_Air_Walk,
                Activity.Reload_Air_Walk_Loop: Activity.Secondary_Reload_Air_Walk_Loop,
                Activity.Reload_Air_Walk_End: Activity.Secondary_Reload_Air_Walk_End
            },

            TFWeaponType.Melee: {
                Activity.Stand: Activity.Melee_Stand,
                Activity.Run: Activity.Melee_Run,
                Activity.Crouch: Activity.Melee_Crouch,
                Activity.Crouch_Walk: Activity.Melee_Crouch_Walk,
                Activity.Swim: Activity.Melee_Swim,
                Activity.Air_Walk: Activity.Melee_Air_Walk,
                Activity.Jump: Activity.Melee_Jump,
                Activity.Jump_Start: Activity.Melee_Jump_Start,
                Activity.Jump_Float: Activity.Melee_Jump_Float,
                Activity.Jump_Land: Activity.Melee_Jump_Land,
                Activity.Double_Jump_Crouch: Activity.Melee_Double_Jump_Crouch,
                Activity.Attack_Stand: Activity.Melee_Attack_Stand,
                Activity.Attack_Crouch: Activity.Melee_Attack_Crouch,
                Activity.Attack_Swim: Activity.Melee_Attack_Swim,
                Activity.Attack_Air_Walk: Activity.Melee_Attack_Air_Walk
            }
        }

    def translateViewModelActivity(self, activity):
        return self.vmActTable[self.weaponType].get(activity, activity)

    def translateActivity(self, activity):
        return self.actTable[self.weaponType].get(activity, activity)

    def activate(self):
        originalPrimaryAttack = self.nextPrimaryAttack
        deploy = True
        DistributedWeaponAI.activate(self)

        if deploy:
            # overrides the anim length for calculating ready time.
            # Don't override primary attacks that are already further out than this.
            # This prevents people from exploiting weapons to allow weapons to fire
            # faster.
            deployTime = 0.67
            self.nextPrimaryAttack = max(originalPrimaryAttack, globalClock.getFrameTime() + deployTime)

        return True

    def primaryAttack(self):
        self.weaponMode = TFWeaponMode.Primary

        #if not self.canAttack():
        #    return

        DistributedWeaponAI.primaryAttack(self)

        self.player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)

        weaponData = self.weaponData.get(self.weaponMode, {})
        origin = self.player.getPos() + (0, 0, self.player.classInfo.ViewHeight)
        angles = self.player.viewAngles
        fireBullets(self.player, origin, angles, self, self.weaponMode, 0, weaponData.get('spread', 0.0), weaponData.get('damage', 1.0))

        self.player.sendUpdate('makeAngry')

        if self.reloadsSingly:
            self.reloadMode = TFReloadMode.Start

    def secondaryAttack(self):
        self.weaponMode = TFWeaponMode.Secondary

        # Don't hook secondary for now.

    def calcIsAttackCritical(self):
        return False

    def reload(self):
        if self.reloadMode == TFReloadMode.Start:
            if self.ammo <= 0:
                return False
            if self.clip >= self.maxClip:
                return False

        if self.reloadsSingly:
            return self.reloadSingly()

        self.defaultReload(self.maxClip, Activity.VM_Reload)

        return True

    def abortReload(self):
        DistributedWeaponAI.abortReload(self)
        self.reloadMode = TFReloadMode.Start

    def reloadSingly(self):
        if self.nextPrimaryAttack > globalClock.getFrameTime():
            return False

        if not self.player:
            return False

        if self.reloadMode == TFReloadMode.Start:
            if self.sendWeaponAnim(Activity.VM_Reload_Start):
                self.setReloadTimer(self.viewModel.getSequenceLength(self.viewModel.getCurrSequence()))
            else:
                self.updateReloadTimers(True)

            self.reloadMode = TFReloadMode.Reloading

            self.reloadStartClipAmount = self.clip

            return True

        elif self.reloadMode == TFReloadMode.Reloading:
            if self.timeWeaponIdle > globalClock.getFrameTime():
                return False

            if self.clip == self.reloadStartClipAmount:
                self.player.doAnimationEvent(PlayerAnimEvent.Reload)
            else:
                self.player.doAnimationEvent(PlayerAnimEvent.ReloadLoop)

            self.reloadedThroughAnimEvent = False

            if self.sendWeaponAnim(Activity.VM_Reload):
                self.setReloadTimer(self.viewModel.getSequenceLength(self.viewModel.getCurrSequence()))
            else:
                self.updateReloadTimers(False)

            # TODO: WEAPON sound reload

            self.reloadMode = TFReloadMode.ReloadingContinue
            return True

        elif self.reloadMode == TFReloadMode.ReloadingContinue:
            # Did we finish the reload start?  Now we can finish reloading the rocket.
            if self.timeWeaponIdle > globalClock.getFrameTime():
                return False

            # If we have ammo, remove ammo and add it to clip.
            if (self.ammo > 0 and not self.reloadedThroughAnimEvent):
                self.clip = min(self.clip + 1, self.maxClip)
                self.ammo -= 1

            if self.clip == self.maxClip or self.ammo <= 0:
                # Clip full or out of ammo to put in.
                self.reloadMode = TFReloadMode.Finish
            else:
                # Still reloading
                self.reloadMode = TFReloadMode.Reloading

            return True

        elif self.reloadMode == TFReloadMode.Finish:
            if self.sendWeaponAnim(Activity.VM_Reload_Finish):
                pass

            self.player.doAnimationEvent(PlayerAnimEvent.ReloadEnd)
            self.reloadMode = TFReloadMode.Start
            return True

    def operator_handleAnimEvent(self, event, operator):
        if event['event'] == AnimEvent.Weapon_IncrementAmmo:
            if self.ammo > 0 and not self.reloadedThroughAnimEvent:
                self.clip = min(self.clip + 1, self.maxClip)
                self.ammo -= 1
            self.reloadedThroughAnimEvent = True
            return

    def defaultReload(self, clipSize, activity):
        if not self.player:
            return False

        # Setup and check for reload.
        reloadPrimary = False
        reloadSecondary = False

        # If you don't have clips, then don't try to reload them.
        if self.usesClip:
            primary = min(clipSize - self.clip, self.ammo)
            if primary != 0:
                reloadPrimary = True

        if self.usesClip2:
            secondary = min(clipSize2 - self.clip2, self.ammo2)
            if secondary != 0:
                reloadSecondary = True

        if not (reloadPrimary or reloadSecondary):
            return False

        # TODO: play reload sound

        # Play the player's reload animation
        self.player.doAnimationEvent(PlayerAnimEvent.Reload)

        reloadTime = 0.0
        if self.sendWeaponAnim(activity):
            reloadTime = self.viewModel.getSequenceLength(self.viewModel.getCurrSequence())
        else:
            # No reload animation. Use the script time.
            if reloadPrimary:
                reloadTime = self.weaponData[TFWeaponMode.Primary]['timeReload']
            else:
                reloadTime = self.weaponData[TFWeaponMode.Secondary]['timeReload']

        self.setReloadTimer(reloadTime)

        self.inReload = True

        return True

    def updateReloadTimers(self, start):
        # Starting a reload?
        if start:
            self.setReloadTimer(self.weaponData[self.weaponMode]['timeReloadStart'])
        else:
            self.setReloadTimer(self.weaponData[self.weaponMode]['timeReload'])

    def setReloadTimer(self, reloadTime):
        if not self.player:
            return

        time = globalClock.getFrameTime() + reloadTime
        # TODO: set next player attack time (weapon independent)
        self.nextPrimaryAttack = time

        # Set next idle time (based on reloading).
        self.timeWeaponIdle = time

    def sendReloadEvents(self):
        if not self.player:
            return

        self.player.doAnimationEvent(PlayerAnimEvent.Reload)

    def itemBusyFrame(self):
        DistributedWeaponAI.itemBusyFrame(self)

        if not self.player:
            return

        if self.player.buttons & InputFlag.Attack2 and not self.inReload and not self.inAttack2:
            if self.player.doClassSpecialSkill():
                self.nextSecondaryAttack = globalClock.getFrameTime() + 0.5
            self.inAttack2 = True
        else:
            self.inAttack2 = False

        # Interrupt a reload on reload singly weapons.
        if self.reloadsSingly:
            if self.player.buttons & InputFlag.Attack1:
                if self.reloadMode != TFReloadMode.Start and self.clip > 0:
                    self.reloadMode = TFReloadMode.Start
                    self.inReload = False
                    self.player.nextAttack = globalClock.getFrameTime()
                    self.nextPrimaryAttack = globalClock.getFrameTime()

                    self.timeWeaponIdle = globalClock.getFrameTime() + self.weaponData[self.weaponMode]['timeIdle']

    def itemPostFrame(self):
        if not self.player:
            return

        # Debounce InAttack flags
        if self.inAttack and not (self.player.buttons & InputFlag.Attack1):
            self.inAttack = False
        if self.inAttack2 and not (self.player.buttons & InputFlag.Attack2):
            self.inAttack2 = False

        if self.lowered:
            return

        DistributedWeaponAI.itemPostFrame(self)

        if self.reloadsSingly:
            self.reloadSinglyPostFrame()

    def reloadSinglyPostFrame(self):
        if self.timeWeaponIdle > globalClock.getFrameTime():
            return

        # If the clip is empty and we have ammo remaining
        if (self.clip == 0 and self.ammo > 0) or (self.reloadMode != TFReloadMode.Start):
            # Reload/continue reloading
            self.reload()

    def weaponIdle(self):
        if self.hasWeaponIdleTimeElapsed():
            if not (self.reloadsSingly and self.reloadMode != TFReloadMode.Start):
                self.sendWeaponAnim(Activity.VM_Idle)
                self.timeWeaponIdle = globalClock.getFrameTime() + self.viewModel.getSequenceLength(self.viewModel.getCurrSequence())

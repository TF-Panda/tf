from .TFWeaponMelee import TFWeaponMelee

from .WeaponMode import TFWeaponMode, TFWeaponType

from tf.tfbase import TFLocalizer
from tf.actor.Activity import Activity

import random

class DistributedFists(TFWeaponMelee):

    WeaponModel = "models/weapons/c_shotgun"
    WeaponViewModel = "models/weapons/v_fist_heavy"
    UsesViewModel = True
    HideWeapon = True
    DropAmmo = False

    VoiceLines = [
      "Heavy.Meleeing01",
      "Heavy.Meleeing02",
      "Heavy.Meleeing03",
      "Heavy.Meleeing04",
      "Heavy.Meleeing05",
      "Heavy.Meleeing06",
      "Heavy.Meleeing07",
      "Heavy.Meleeing08"
    ]

    def __init__(self):
        TFWeaponMelee.__init__(self)
        self.weaponType = TFWeaponType.Melee
        self.weaponData[TFWeaponMode.Primary].update({
          'damage': 65,
          'timeFireDelay': 0.8,
          'smackDelay': 0.2,
          'timeIdle': 5.0
        })
        self.weaponData[TFWeaponMode.Secondary] = self.weaponData[TFWeaponMode.Primary]

        if not IS_CLIENT:
            self.lastSpeakTime = 0.0
            self.speakIval = 0.0

    def primaryAttack(self):
        #if not self.canAttack():
        #    return

        self.weaponMode = TFWeaponMode.Primary
        self.punch()

    def secondaryAttack(self):
        #if not self.canAttack():
        #    return
        self.weaponMode = TFWeaponMode.Secondary
        self.punch()

    def punch(self):
        if not self.player:
            return

        self.swing()

        if not IS_CLIENT:
            self.player.pushExpression('specialAction')

        self.nextSecondaryAttack = self.nextPrimaryAttack

        if not IS_CLIENT:
            self.speakWeaponFire()

    def speakWeaponFire(self):
        now = base.clockMgr.getTime()
        elapsed = now - self.lastSpeakTime
        if elapsed >= self.speakIval:
            line = random.choice(self.VoiceLines)
            self.player.d_speak(line)
            self.lastSpeakTime = now
            self.speakIval = random.uniform(4.0, 8.0)

    def doViewModelAnimation(self):
        if self.weaponMode == TFWeaponMode.Primary:
            act = Activity.VM_Hit_Left
        else:
            act = Activity.VM_Hit_Right
        self.sendWeaponAnim(act)

    def getSingleSound(self):
        return "Weapon_Fist.Miss"

    def getHitPlayerSound(self):
        return "Weapon_Fist.HitFlesh"

    def getHitWorldSound(self):
        return "Weapon_Fist.HitWorld"

    def getName(self):
        return TFLocalizer.Fists

if not IS_CLIENT:
    DistributedFistsAI = DistributedFists
    DistributedFistsAI.__name__ = 'DistributedFistsAI'


from panda3d.core import Vec3, Quat, NodePath
from panda3d.pphysics import PhysSweepResult, PhysRayCastResult

from .TFWeapon import TFWeapon

from .WeaponMode import TFWeaponMode
from .TakeDamageInfo import TakeDamageInfo, applyMultiDamage, clearMultiDamage, calculateMeleeDamageForce
from tf.actor.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.tfbase.TFGlobals import DamageType
from tf.tfbase import TFFilters, CollisionGroups

from tf.tfbase.SurfaceProperties import SurfaceProperties, SurfacePropertiesByPhysMaterial

SWING_MINS = Vec3(-18)
SWING_MAXS = Vec3(18)

tf_meleeattackforcescale = 80.0

class TFWeaponMelee(TFWeapon):

    def __init__(self):
        TFWeapon.__init__(self)
        self.usesAmmo = False
        self.usesAmmo2 = False
        self.usesClip = False
        self.usesClip2 = False
        self.meleeWeapon = True
        self.connected = False
        self.smackTime = -1.0
        self.currentAttackIsCritical = False

    def deactivate(self):
        self.smackTime = -1.0
        TFWeapon.deactivate(self)

    def primaryAttack(self):
        self.weaponMode = TFWeaponMode.Primary
        self.connected = False
        self.currentAttackIsCritical = False

        self.swing()

        if not IS_CLIENT:
            self.player.pushExpression('specialAction')

        # TODO: speak weapon fire

    def secondaryAttack(self):
        if self.inAttack2:
            return

        self.player.doClassSpecialSkill()
        self.inAttack2 = True
        self.nextSecondaryAttack = globalClock.frame_time + 0.5

    def doViewModelAnimation(self):
        self.sendWeaponAnim(Activity.VM_Fire)

    def doPlayerAnimation(self, player):
        player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)

    def swing(self):
        player = self.player

        self.doPlayerAnimation(player)
        self.doViewModelAnimation()

        self.nextPrimaryAttack = globalClock.frame_time + self.weaponData[self.weaponMode]['timeFireDelay']
        self.timeWeaponIdle = self.nextPrimaryAttack + self.weaponData[self.weaponMode]['timeIdleEmpty']

        self.playSound(self.getSingleSound())

        self.smackTime = globalClock.frame_time + self.weaponData[self.weaponMode]['smackDelay']

    def itemPostFrame(self):
        # check for smack
        if self.smackTime > 0.0 and globalClock.frame_time > self.smackTime:
            self.smack()
            self.smackTime = -1.0

        TFWeapon.itemPostFrame(self)

    def doSwingTrace(self):

        # Setup swing range
        q = Quat()
        q.setHpr(self.player.viewAngles)
        forward = q.getForward()
        swingStart = self.player.getEyePosition()
        swingEnd = swingStart + (forward * 48)

        # See if we hit anything.
        filter = TFFilters.TFQueryFilter(self.player)
        mask = CollisionGroups.World | CollisionGroups.Mask_AllTeam | CollisionGroups.HitBox
        tr = TFFilters.traceLine(swingStart, swingEnd, mask, filter)

        if tr['hit']:
            return tr

        return TFFilters.traceBox(swingStart, swingEnd, SWING_MINS, SWING_MAXS,
                                  mask, filter)

    def getMeleeDamage(self, target):
        return self.weaponData[self.weaponMode]['damage']

    def smack(self):
        if not IS_CLIENT:
            base.air.lagComp.startLagCompensation(self.player, self.player.currentCommand)

        self.syncAllHitBoxes()

        tr = self.doSwingTrace()
        if tr['hit']:
            ent = tr['ent']
            if ent and ent.isPlayer():
                self.playSound(self.getHitPlayerSound())
            else:
                self.playSound(self.getHitWorldSound())

            physMat = tr['mat']
            surfaceDef = SurfacePropertiesByPhysMaterial.get(physMat)
            if not surfaceDef:
                surfaceDef = SurfaceProperties['default']

            if IS_CLIENT and (ent is not None) and base.cr.prediction.isFirstTimePredicted():
                ent.traceDecal(surfaceDef.impactDecal, tr)

            if not IS_CLIENT and (ent is not None):
                ent.traceDecal(surfaceDef.impactDecal, tr, excludeClients=[self.player.owner])
                dmgType = DamageType.Bullet | DamageType.NeverGib | DamageType.Club
                damage = self.getMeleeDamage(ent)
                if damage > 0:
                    if self.currentAttackIsCritical:
                        dmgType |= DamageType.Critical
                    customDamage = -1
                    info = TakeDamageInfo()
                    info.attacker = self.player
                    info.inflictor = self.player
                    info.setDamage(damage)
                    info.damageType = dmgType
                    calculateMeleeDamageForce(info, tr['tracedir'], tr['endpos'], 1.0 / damage * tf_meleeattackforcescale)
                    ent.dispatchTraceAttack(info, tr['tracedir'], tr)
                    applyMultiDamage()

                self.onEntityHit(ent)

        if not IS_CLIENT:
            base.air.lagComp.finishLagCompensation(self.player)

    def onEntityHit(self, ent):
        pass


if not IS_CLIENT:
    TFWeaponMeleeAI = TFWeaponMelee
    TFWeaponMeleeAI.__name__ = 'TFWeaponMeleeAI'

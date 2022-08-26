"""DistributedMedigun module: contains the DistributedMedigun class."""


from panda3d.core import *
from panda3d.physics import *

from .TFWeaponGun import TFWeaponGun

from tf.tfbase import TFLocalizer

from .WeaponMode import TFWeaponMode, TFWeaponType
from tf.tfbase.TFGlobals import DamageType, Contents, CollisionGroup, TFTeam
from tf.tfbase import TFFilters
from tf.player.InputButtons import InputFlag
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.actor.Activity import Activity

# heal()
# recalculateInvuln()
# takeHealth()
# getMaxBuffedHealth()
# getNumHealers()
# stopHealing()

class DistributedMedigun(TFWeaponGun):

    WeaponModel = "models/weapons/w_medigun"
    WeaponViewModel = "models/weapons/v_medigun_medic"
    UsesViewModel = True

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.weaponData[TFWeaponMode.Primary].update({
            'damage': 24,
            'range': 450,
            'timeFireDelay': 0.5,
            'timeIdle': 5.0,
            'timeIdleEmpty': 0.25,
            'timeReloadStart': 0.1,
            'timeReload': 0.5
        })
        self.healEffectLifetime = 0
        self.healing = False
        self.attacking = False
        self.holstered = True
        self.chargeRelease = True
        self.healingTargetId = -1

        self.healSound = None
        self.healParticle = None
        self.healBeamSourceNode = None

        self.deploying = False

        self.nextBuzzTime = 0
        self.releaseStartedAt = 0
        self.chargeLevel = 0.0

        self.usesAmmo = False
        self.usesClip = False
        self.reloadsSingly = False
        self.weaponType = TFWeaponType.Secondary

        self.lastRejectSoundTime = 0.0

    if IS_CLIENT:
        def addPredictionFields(self):
            TFWeaponGun.addPredictionFields(self)

            self.addPredictionField("healing", bool)
            self.addPredictionField("attacking", bool)
            self.addPredictionField("holstered", bool)
            self.addPredictionField("deploying", bool, networked=False, noErrorCheck=True)
            self.addPredictionField("healingTargetId", int)
            self.addPredictionField("chargeLevel", float)
            self.addPredictionField("chargeRelease", bool)
            self.addPredictionField("lastRejectSoundTime", float, networked=False, noErrorCheck=True)

    def allowedToHealTarget(self, target):
        return target.team == self.player.team

    def couldHealTarget(self, target):
        if target and not target.isDODeleted() and target.isPlayer() and not target.isDead() and not self.isHealingTarget(target):
            return self.allowedToHealTarget(target)

        return False

    def getHealingTarget(self):
        target = base.net.doId2do.get(self.healingTargetId)
        if target and target.isDODeleted():
            return None
        return target

    def isHealingTarget(self, target):
        return self.getHealingTarget() == target

    def getHealRate(self):
        return self.weaponData[self.weaponMode]['damage']

    def getTargetRange(self):
        return self.weaponData[self.weaponMode]['range']

    def getStickRange(self):
        return self.getTargetRange() * 1.2

    def maintainTargetInSlot(self):
        target = self.getHealingTarget()

        src = self.player.getEyePosition()
        targetPoint = target.getWorldSpaceCenter()

        dist = (targetPoint - src).length()
        if dist < self.getStickRange():
            if self.nextTargetCheckTime > globalClock.frame_time:
                return

            self.nextTargetCheckTime = globalClock.frame_time + 1.0

            q = Quat()
            q.setHpr(self.player.viewAngles)
            vecAiming = q.getForward()

            vecEnd = src + vecAiming * self.getTargetRange()

            filter = TFFilters.TFQueryFilter(self.player)
            tr = TFFilters.traceLine(src, vecEnd, Contents.Solid | Contents.AnyTeam,
                                     0, filter)
            # Still visible?
            if tr['ent'] == target:
                return

            tr = TFFilters.traceLine(src, targetPoint, Contents.Solid | Contents.AnyTeam,
                                     0, filter)
            if (not tr['hit']) or (tr['ent'] == target):
                return

            # If we failed, try the target's eye point as well.
            tr = TFFilters.traceLine(src, target.getEyePosition(), Contents.Solid | Contents.AnyTeam,
                                     0, filter)
            if (not tr['hit']) or (tr['ent'] == target):
                return

        # We've lost this guy.
        self.removeHealingTarget()

    def findNewTargetForSlot(self):
        src = self.player.getEyePosition()
        if self.getHealingTarget():
            self.removeHealingTarget()

        # In normal mode, we heal players under our croshair
        q = Quat()
        q.setHpr(self.player.viewAngles)
        vecAiming = q.getForward()

        # Find a player in range of this player, and make sure they're healable.
        vecEnd = src + vecAiming * self.getTargetRange()

        filter = TFFilters.TFQueryFilter(self.player)
        tr = TFFilters.traceLine(src, vecEnd, Contents.Solid | Contents.AnyTeam, 0, filter)
        if tr['hit'] and tr['ent']:
            if self.couldHealTarget(tr['ent']):
                if not IS_CLIENT:
                    self.addTask(self.__healTargetThink, 'healTargetThink', appendTask=True, sim=True)
                self.healingTargetId = tr['ent'].doId
                self.nextTargetCheckTime = globalClock.frame_time + 1.0

    if not IS_CLIENT:

        def __healTargetThink(self, task):
            target = self.getHealingTarget()
            if not target or target.isDODeleted() or target.isDead():
                self.healingTargetId = -1
                return task.done

            owner = self.player

            time = globalClock.frame_time - owner.getTimeBase()
            if time > 5.0 or not self.allowedToHealTarget(target):
                self.removeHealingTarget(True)

            task.delayTime = 0.2
            return task.again

    def findAndHealTargets(self):

        found = False
        target = self.getHealingTarget()
        if target and not target.isDODeleted() and not target.isDead():
            self.maintainTargetInSlot()
        else:
            self.findNewTargetForSlot()

        newTarget = self.getHealingTarget()
        if newTarget and not newTarget.isDODeleted() and not newTarget.isDead():
            if not IS_CLIENT:
                if target != newTarget and newTarget.isPlayer():
                    newTarget.heal(self.player, self.getHealRate())

                newTarget.recalculateInvuln(False)

                if self.releaseStartedAt and self.releaseStartedAt < (globalClock.frame_time + 0.2):
                    # When we release, everyone we heal rockets to full health.
                    newTarget.takeHealth(newTarget.maxHealth)


            found = True

            # Charge our power if we're not releasing it, and our target
            # isn't receiving any benefit from our healing.
            if not self.chargeRelease:
                boostMax = math.floor(newTarget.getMaxBuffedHealth() * 0.95)

                chargeAmount = globalClock.dt / weapon_medigun_charge_rate

                # Reduce charge for healing fully healed guys
                if newTarget.health >= boostMax and (not base.game.inSetup()):
                    chargeAmount *= 0.5

                totalHealers = newTarget.getNumHealers()
                if totalHealers > 1:
                    chargeAmount /= totalHealers

                newLevel = min(self.chargeLevel + chargeAmount, 1.0)
                #if not IS_CLIENT:
                #    if newLevel >= 1.0 and self.chargeLevel < 1.0:

                self.chargeLevel = newLevel

        return found

    def activate(self):
        if TFWeaponGun.activate(self):
            self.deploying = True
            self.holstered = False
            self.nextTargetCheckTime = globalClock.frame_time
            if IS_CLIENT:
                self.addTask(self.__weaponSoundUpdate, 'medigunSound', appendTask=True, sim=True)
            return True
        return False

    def deactivate(self):
        self.removeHealingTarget(True)
        self.attacking = False
        self.holstered = True
        self.deploying = False
        if IS_CLIENT:
            self.removeTask('medigunSound')
            if self.healSound:
                self.healSound.stop()
                self.healSound = None
            if self.healParticle:
                self.healParticle.softStop()
                self.healParticle = None
            self.healBeamSourceNode = None
        TFWeaponGun.deactivate(self)

    def isHealingTargetValid(self):
        return self.getHealingTarget() is not None

    def removeHealingTarget(self, stopHealingSelf=False):
        if not self.player:
            return

        if not IS_CLIENT:
            if self.isHealingTargetValid():
                target = self.getHealingTarget()
                if target.isPlayer():
                    target.stopHealing(self.player)
                    target.recalculateInvuln(False)
                    target.speakHealed()

            self.removeTask('healTargetThink')

        self.healingTargetId = -1
        if self.healing:
            self.sendWeaponAnim(Activity.VM_Post_Fire)
            self.player.doAnimationEvent(PlayerAnimEvent.AttackPost)

        self.healing = False

    def primaryAttack(self):
        if self.findAndHealTargets():
            if not self.healing:
                self.sendWeaponAnim(Activity.VM_Pre_Fire)
                self.player.doAnimationEvent(PlayerAnimEvent.AttackPre)

            self.healing = True
        else:
            if IS_CLIENT:
                if globalClock.frame_time >= self.lastRejectSoundTime + 0.5:
                    if base.cr.prediction.firstTimePredicted:
                        self.player.emitSound("Player.UseDeny")
                    self.lastRejectSoundTime = globalClock.frame_time
            self.removeHealingTarget(False)

    def secondaryAttack(self):
        if self.chargeLevel < 1.0 or self.chargeRelease:
            if IS_CLIENT:
                # Deny, flash.
                if not self.chargeRelease and self.flashCharge <= 0:
                    self.flashCharge = 10
                    self.player.emitSound("Player.DenyWeaponSelection")
            return

        #if self.player.hasFlag():
        #    self.player.emitSound("Player.DenyWeaponSelection")
        #    return

        self.chargeRelease = False
        self.releaseStartedAt = 0

    def itemPostFrame(self):
        if not self.deploying:
            self.attacking = False
            if self.player.buttons & InputFlag.Attack1:
                self.primaryAttack()
                self.attacking = True
            elif self.healing:
                self.removeHealingTarget()

        self.weaponIdle()

    def weaponIdle(self):
        if self.hasWeaponIdleTimeElapsed():
            if self.healing:
                self.sendWeaponAnim(Activity.VM_Fire)
                self.player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)
                return
            if self.deploying:
                self.deploying = False

            return TFWeaponGun.weaponIdle(self)

    if IS_CLIENT:
        def makeHealBeamParticle(self):
            if self.isOwnedByLocalPlayer():
                self.healBeamSourceNode = self.player.viewModel.find("**/muzzle")
            else:
                self.healBeamSourceNode = self.player.find("**/muzzle")

            healBeamTargetNode = self.getHealingTarget().attachNewNode("healTarget")
            healBeamTargetNode.setPos(0, 0, 48)

            sys = ParticleSystem2()
            sys.setPoolSize(166)
            sys.setInput(0, self.healBeamSourceNode, False) # medigun muzzle
            sys.setInput(1, healBeamTargetNode, True) # heal target

            emitter = ContinuousParticleEmitter()
            emitter.setEmissionRate(150)
            sys.addEmitter(emitter)

            sys.addInitializer(P2_INIT_PositionSphereVolume((0, 0, 0), 0.1, 0.1, Vec3(1, 0, 1)))
            sys.addInitializer(P2_INIT_LifespanRandomRange(1, 1))
            sys.addInitializer(P2_INIT_ScaleRandomRange(Vec3(6), Vec3(6)))
            if self.player.team == TFTeam.Red:
                sys.addInitializer(P2_INIT_ColorRandomRange(Vec3(255/255, 90/255, 90/255), Vec3(255/255, 126/255, 93/255)))
            else:
                sys.addInitializer(P2_INIT_ColorRandomRange(Vec3(0/255, 159/255, 165/255), Vec3(116/255, 152/255, 255/255)))
            sys.addInitializer(P2_INIT_RotationVelocityRandomRange(96, 96))

            scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
            l0 = ParticleLerpSegment()
            l0.type = l0.LTLinear
            l0.start = 0.0
            l0.end = 1.0
            l0.start_is_initial = True
            l0.end_value = Vec3(1.0)
            scaleLerp.addSegment(l0)
            sys.addFunction(scaleLerp)

            colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
            l0 = ParticleLerpSegment()
            l0.type = l0.LTLinear
            l0.start = 0.0
            l0.end = 1.0
            l0.start_is_initial = True
            if self.player.team == TFTeam.Red:
                l0.end_value = Vec3(255/255, 90/255, 0/255)
            else:
                l0.end_value = Vec3(48/255, 141/255, 255/255)
            colorLerp.addSegment(l0)
            sys.addFunction(colorLerp)

            sys.addFunction(LinearMotionParticleFunction())
            sys.addFunction(AngularMotionParticleFunction())
            sys.addFunction(LifespanKillerParticleFunction())

            twist = CylinderVortexParticleForce(512.0, (0, 1, 0))
            twist.setLocalAxis(False)
            twist.setInput0(0)
            twist.setInput1(1)
            twist.setMode(twist.AMVecBetweenInputs)
            sys.addForce(twist)

            const = PathParticleConstraint()
            const.start_input = 0
            const.end_input = 1
            const.max_distance = 2
            const.mid_point = 0.1
            const.min_distance = 2
            const.bulge_control = 1
            const.random_bulge = 1.3
            const.travel_time = 1.0
            sys.addConstraint(const)

            renderer = SpriteParticleRenderer2()
            state = RenderState.make(MaterialAttrib.make(loader.loadMaterial("tfmodels/src/materials/medicbeam_curl.pmat")),
                         ColorAttrib.makeVertex())
            renderer.setRenderState(state)
            sys.addRenderer(renderer)

            return sys

        def __weaponSoundUpdate(self, task):
            if self.isActiveLocalPlayerWeapon() and base.cr.prediction.inPrediction and not base.cr.prediction.firstTimePredicted:
                return task.cont

            if self.healingTargetId != -1:
                if not self.healSound:
                    if self.isOwnedByLocalPlayer():
                        # We are healing someone.
                        self.healSound = self.emitSound("WeaponMedigun.HealingHealer", loop=True)
                    elif self.healingTargetId == base.localAvatarId:
                        self.healSound = self.emitSoundSpatial("WeaponMedigun.HealingTarget", loop=True, offset=(0, 0, 32))
                    else:
                        self.healSound = self.emitSoundSpatial("WeaponMedigun.HealingWorld", loop=True, offset=(0, 0, 32))

                if not self.healParticle:
                    self.healParticle = self.makeHealBeamParticle()
                    self.healParticle.start(base.dynRender)

            else:
                if self.healSound:
                    self.healSound.stop()
                    self.healSound = None
                if self.healParticle:
                    self.healParticle.softStop()
                    self.healParticle = None
                self.healBeamSourceNode = None

            return task.cont

    def getName(self):
        return TFLocalizer.MediGun

    def getSingleSound(self):
        return "WeaponMedigun.Healing"

    def getEmptySound(self):
        return "Weapon_Pistol.Empty"

    def getReloadSound(self):
        return "Weapon_Pistol.WorldReload"

if not IS_CLIENT:
    DistributedMedigunAI = DistributedMedigun
    DistributedMedigunAI.__name__ = 'DistributedMedigunAI'

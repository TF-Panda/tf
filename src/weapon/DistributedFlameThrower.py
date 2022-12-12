"""DistributedFlameThrower module: contains the DistributedFlameThrower class."""

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFWeaponMode, TFWeaponType

from tf.player.InputButtons import InputFlag
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.actor.Actor import Actor
from tf.actor.Activity import Activity
from tf.tfbase import TFLocalizer, Sounds, TFFilters, TFGlobals, CollisionGroups
from tf.weapon.TakeDamageInfo import TakeDamageInfo
from direct.directbase import DirectRender

from panda3d.core import Vec3, Quat, Point3

import random

FLAME_VELOCITY = 2300
FLAME_DRAG = 0.89
FLAME_FLOAT = 50
FLAME_TIME = 0.5
FLAME_VECRAND = 0.05
FLAME_BOXSIZE = 8
FLAME_MAXDAMAGEDIST = 350
FLAME_SHORTRANGEDAMAGEMULT = 1.2
FLAME_VELOCITYFADESTART = 0.3
FLAME_VELOCITYFADEEND = 0.5
FLAME_START_SCALE = 16.0
FLAME_END_SCALE = 80.0

class FlameProjectile:

    FlameModel = None

    def __init__(self, shooter, src, dir):
        self.shooter = shooter
        self.srcPos = Point3(src)
        self.pos = Point3(src)
        self.dir = dir
        self.damageAmount = 0.0

        self.baseVelocity = self.dir * FLAME_VELOCITY
        randomMin = -FLAME_VELOCITY * FLAME_VECRAND
        randomMax = FLAME_VELOCITY * FLAME_VECRAND
        self.baseVelocity += Vec3(random.uniform(randomMin, randomMax),
                                  random.uniform(randomMin, randomMax),
                                  random.uniform(randomMin, randomMax))
        self.attackerVelocity = Vec3(self.shooter.velocity)
        self.velocity = Vec3(self.baseVelocity)

        self.size = Vec3(FLAME_BOXSIZE)
        self.hitEnts = set()
        self.team = self.shooter.team
        self.task = base.simTaskMgr.add(self.__flameUpdate, 'flameUpdate')
        self.filter = TFFilters.TFQueryFilter(self.shooter)

        self.startTime = globalClock.frame_time
        self.killTime = self.startTime + FLAME_TIME
        self.wasBlocked = False

        if IS_CLIENT:
            if not self.FlameModel:
                self.FlameModel = base.loader.loadModel("models/effects/explosion").find("**/+SequenceNode")
            self.explScale = 20.0
            flame = self.FlameModel.copyTo(base.dynRender)
            flame.setPos(src)
            flame.hide(DirectRender.ShadowCameraBitmask)
            duration = flame.node().getNumFrames() / flame.node().getFrameRate()
            flame.node().setPlayRate(duration / FLAME_TIME)
            flame.node().play()
            flame.setBillboardPointEye()
            self.flame = flame

    def __flameUpdate(self, task):
        self.update()
        return task.cont

    def kill(self):
        if self.task:
            self.task.remove()
            self.task = None
        self.filter = None
        self.shooter = None
        self.hitEnts = None
        if IS_CLIENT:
            if self.flame:
                self.flame.removeNode()
                self.flame = None

    def update(self):
        origDt = globalClock.dt
        globalClock.dt = base.intervalPerTick

        if globalClock.frame_time >= self.killTime:
            globalClock.dt = origDt
            self.kill()
            return

        elapsed = globalClock.frame_time - self.startTime
        frac = max(0.0, min(1.0, elapsed / FLAME_TIME))

        if not self.wasBlocked:
            attackerVelocityBlend = TFGlobals.remapValClamped(elapsed, FLAME_VELOCITYFADESTART,
                FLAME_VELOCITYFADEEND, 1.0, 0.0)

            self.baseVelocity *= FLAME_DRAG

            # Add our float upward velocity.
            velocity = self.baseVelocity + Vec3(0, 0, FLAME_FLOAT) + (self.attackerVelocity * attackerVelocityBlend)

            # Update our velocity.
            self.velocity = Vec3(velocity)

        # Now clip the velocity.
        oldPos = Vec3(self.pos)
        blocked = TFFilters.collideAndSlide(
            self.pos, self.velocity, {'type': 'sphere', 'radius': FLAME_BOXSIZE},
            CollisionGroups.World, self.filter)
        if blocked:
            self.wasBlocked = True

        if not IS_CLIENT:
            tr = TFFilters.traceBox(oldPos, self.pos, -self.size, self.size, CollisionGroups.Mask_AllTeam,
                                    self.filter)
            ent = tr['ent']
            if tr['hit'] and ent:
                #if not ent.isPlayer() and not ent.isObject():
                    # Kill the flame if we hit a non-player or object.
                #    self.kill()
                #    return

                if ent not in self.hitEnts:
                    self.hitEnts.add(ent)
                    if not ent.isDead() and ent.team != self.team:

                        dmgDist = (self.pos - self.srcPos).length()
                        if dmgDist <= 125:
                            # At very short range, apply short range damage multiplier
                            mult = FLAME_SHORTRANGEDAMAGEMULT
                        else:
                            mult = TFGlobals.remapValClamped(dmgDist, FLAME_MAXDAMAGEDIST*0.5, FLAME_MAXDAMAGEDIST, 1.0, 0.25)
                        dmg = self.damageAmount * mult
                        dmg = max(dmg, 1.0)

                        info = TakeDamageInfo()
                        info.inflictor = self.shooter
                        info.attacker = self.shooter
                        info.damageType = TFGlobals.DamageType.Ignite | TFGlobals.DamageType.PreventPhysicsForce
                        info.setDamage(dmg)
                        ent.takeDamage(info)
                        #if ent.isPlayer():
                       #     ent.burn(self.shooter)
                        #base.world.emitSoundSpatial("Weapon_FlameThrower.FireHit", self.pos)
        else:
            self.flame.setPos(self.pos)
            self.flame.setScale((FLAME_START_SCALE / self.explScale) * (1.0 - frac) + (FLAME_END_SCALE / self.explScale) * frac)

        globalClock.dt = origDt

class DistributedFlameThrower(TFWeaponGun):

    WeaponModel = "models/weapons/c_flamethrower"
    WeaponViewModel = "models/weapons/c_flamethrower"
    UsesViewModel = False

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.usesClip = False
        self.usesAmmo = True
        self.maxAmmo = 200
        self.ammo = self.maxAmmo
        self.primaryAttackInterval = 0.105
        self.dmgPerSec = 100
        self.weaponData[TFWeaponMode.Primary].update({
          'damage': 100, # per second
          'timeFireDelay': 0.105,
          'timeIdle': 0.6,
          'timeIdleEmpty': 0.6
        })

        self.isFiring = False
        self.wasFiring = False
        self.startFireTime = 0.0

        self.currFireSound = -1
        self.firingSound = None

        self.pilotLight = None
        self.pilotLightVM = None

    if IS_CLIENT:
        def getVMMuzzlePosWorld(self):
            vm = self.viewModelChar
            charTs = vm.characterNp.getNetTransform()
            attachTs = vm.getAttachment("muzzle", net=False, update=False)
            mat = attachTs.getMat() * charTs.getMat()
            pos = mat.getRow3(3)
            return pos

        def doFlame(self, src, dir):
            #src = Point3(src[0], src[1], src[2])
            if self.isOwnedByLocalPlayer():
                src = self.getVMMuzzlePosWorld()
            else:
                src = self.getMuzzlePosWorld()
            dir = Vec3(dir[0], dir[1], dir[2])
            FlameProjectile(self.player, src, dir)

        def generate(self):
            TFWeaponGun.generate(self)
            #self.flameModel = base.loader.loadModel("models/effects/explosion").find("**/+SequenceNode")
            self.pilotLight = Actor()
            self.pilotLight.loadModel("models/weapons/c_flamethrower_pilotlight", False)
            self.pilotLightVM = Actor()
            self.pilotLightVM.loadModel("models/weapons/c_flamethrower_pilotlight", False)

        def delete(self):
            TFWeaponGun.delete(self)
            if self.pilotLight:
                self.pilotLight.cleanup()
                self.pilotLight = None
            if self.pilotLightVM:
                self.pilotLightVM.cleanup()
                self.pilotLightVM = None

        def preDataUpdate(self):
            TFWeaponGun.preDataUpdate(self)
            if not self.predictable:
                self.wasFiring = self.isFiring

        def addPredictionFields(self):
            TFWeaponGun.addPredictionFields(self)
            self.addPredictionField("isFiring", bool, networked=True)
            self.addPredictionField("startFireTime", float, networked=True, tolerance=0.01)
            self.addPredictionField("wasFiring", bool, networked=False)

        def emitSoundWpn(self, sndName, loop=False, chan=None):
            if self.isOwnedByLocalPlayer():
                return self.emitSound(sndName, loop=loop, chan=chan)
            else:
                return self.emitSoundSpatial(sndName, (0, 0, 30), loop=loop, chan=chan)

        def __weaponSoundUpdateTask(self, task):
            self.weaponSoundUpdate()
            return task.cont

        def weaponSoundUpdate(self):

            loop = False
            sound = -1
            if self.isFiring:
                elapsed = globalClock.frame_time - self.startFireTime
                if elapsed < 3:
                    sound = 0
                    sndName = "Weapon_FlameThrower.FireStart"
                else:
                    sound = 1
                    sndName = "Weapon_FlameThrower.FireLoop"
                    loop = True
            elif self.wasFiring:
                sound = 2
                sndName = "Weapon_FlameThrower.FireEnd"

            if sound != -1 and sound != self.currFireSound:
                if self.firingSound:
                    self.firingSound.stop()
                    self.firingSound = None
                self.firingSound = self.emitSoundWpn(sndName, loop=loop)
                self.currFireSound = sound

    def getName(self):
        return TFLocalizer.FlameThrower

    def activate(self):
        TFWeaponGun.activate(self)
        self.isFiring = False
        self.startFireTime = 0.0
        if IS_CLIENT:
            if not self.isOwnedByLocalPlayer() or base.cr.prediction.isFirstTimePredicted():
                self.emitSoundWpn("Weapon_FlameThrower.PilotLoop")

            if not self.isOwnedByLocalPlayer():
                self.addTask(self.__weaponSoundUpdateTask, 'flameThrowerSoundUpdate', appendTask=True, sim=True)
                if self.player:
                    self.pilotLight.modelNp.reparentTo(self.player)
                    self.pilotLight.setJointMergeParent(self.player)
            else:
                if self.viewModel:
                    self.pilotLightVM.modelNp.reparentTo(self.viewModel)
                    self.pilotLightVM.setJointMergeParent(self.viewModel)

    def deactivate(self):
        if IS_CLIENT:
            if self.firingSound:
                self.firingSound.stop()
                self.firingSound = None
            self.currFireSound = -1
            self.removeTask('flameThrowerSoundUpdate')
            if self.isOwnedByLocalPlayer():
                self.pilotLightVM.modelNp.reparentTo(base.hidden)
            else:
                self.pilotLight.modelNp.reparentTo(base.hidden)
        self.isFiring = False
        self.startFireTime = 0.0
        TFWeaponGun.deactivate(self)

    def primaryAttack(self):
        self.nextPrimaryAttack = globalClock.frame_time + self.primaryAttackInterval
        if self.isFiring:
            self.ammo -= 1

    #def weaponIdle(self):
    #    if self.hasWeaponIdleTimeElapsed():
    #        if self.isFiring:
    #            self.player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)
    #            self.timeWeaponIdle = globalClock.frame_time + 1.0

    if not IS_CLIENT:
        def fireFlame(self):
            src = self.getMuzzlePosWorld()
            _, q = self.getProjectileFireSetup(self.player, Vec3(0), False, src)
            dir = q.getForward()
            proj = FlameProjectile(self.player, src, dir)
            flameIval = 0.075
            proj.damageAmount = self.dmgPerSec * flameIval
            self.nextFlameFireTime = globalClock.frame_time + flameIval
            self.sendUpdate('doFlame', [src, dir])

    def getMuzzlePosWorld(self):
        charTs = self.characterNp.getNetTransform()
        attachTs = self.getAttachment("muzzle", net=False, update=False)
        mat = attachTs.getMat() * charTs.getMat()
        pos = mat.getRow3(3)
        return pos

    def checkGoodToFire(self):
        # If there is a LOS to the player's eyes from the weapon muzzle,
        # we're good to fire flames.
        #print("trace from", self.getMuzzlePosWorld(), "to", self.player.getEyePosition())
        tr = TFFilters.traceLine(self.getMuzzlePosWorld(), self.player.getEyePosition(),
            CollisionGroups.World, TFFilters.TFQueryFilter(self.player))
        #print(tr['hit'], tr['ent'])
        return not tr['hit']

    def itemPostFrame(self):
        self.wasFiring = self.isFiring

        goodToFire = self.ammo > 0 and (self.player.buttons & InputFlag.Attack1)
        if goodToFire:
            goodToFire = self.checkGoodToFire()
            #print("good to fire", goodToFire)

        if goodToFire:
            if not self.isFiring and globalClock.frame_time >= self.nextPrimaryAttack:
                self.isFiring = True
                self.startFireTime = globalClock.frame_time
                self.sendWeaponAnim(Activity.VM_Fire)
                self.nextFlameFireTime = globalClock.frame_time
                self.player.doAnimationEvent(PlayerAnimEvent.AttackPre)
                #self.timeWeaponIdle = globalClock.frame_time + 0.5

        elif self.isFiring:
            self.sendWeaponAnim(Activity.VM_Idle)
            self.isFiring = False
            self.player.doAnimationEvent(PlayerAnimEvent.AttackPost)

        TFWeaponGun.itemPostFrame(self)

        if IS_CLIENT:
            if base.cr.prediction.isFirstTimePredicted():
                self.weaponSoundUpdate()

        if not IS_CLIENT:
            if self.isFiring and globalClock.frame_time >= self.nextFlameFireTime:
                self.fireFlame()

if not IS_CLIENT:
    DistributedFlameThrowerAI = DistributedFlameThrower
    DistributedFlameThrowerAI.__name__ = 'DistributedFlameThrowerAI'

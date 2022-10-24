"""DistributedFlameThrower module: contains the DistributedFlameThrower class."""

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFWeaponMode, TFWeaponType

from tf.player.InputButtons import InputFlag
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.actor.Actor import Actor
from tf.actor.Activity import Activity
from tf.tfbase import TFLocalizer, Sounds, TFFilters, TFGlobals
from tf.weapon.TakeDamageInfo import TakeDamageInfo

from panda3d.core import Vec3, Quat

class FlameProjectile:

    def __init__(self, shooter, src, dir):
        self.shooter = shooter
        self.srcPos = src
        self.pos = src
        self.dir = dir
        self.startSize = Vec3(8)
        self.endSize = Vec3(32)
        self.life = 0.0
        self.duration = 1.0
        self.hitEnts = set()
        self.team = self.shooter.team
        self.task = base.simTaskMgr.add(self.__flameUpdate, 'flameUpdate')

    def __flameUpdate(self, task):
        self.update()
        return task.cont

    def kill(self):
        if self.task:
            self.task.remove()
            self.task = None
        self.shooter = None

    def update(self):
        self.life += globalClock.dt

        if self.life >= self.duration:
            self.kill()
            return

        oldPos = Vec3(self.pos)
        self.pos += self.dir * globalClock.dt * 256.0

        dist = (self.pos - oldPos).length()

        frac = self.life / self.duration

        size = self.startSize * (1.0 - frac) + self.endSize * frac
        mins = oldPos - size
        maxs = oldPos + size

        tr = TFFilters.traceBox(mins, maxs, self.dir, dist, TFGlobals.Contents.Solid | TFGlobals.Contents.AnyTeam,
                                0, TFFilters.TFQueryFilter(self.shooter))
        if tr['hit'] and tr['ent']:
            ent = tr['ent']
            if not ent.isPlayer() and not ent.isObject():
                # Kill the flame if we hit a non-player or object.
                self.kill()
                return

            if ent not in self.hitEnts:
                self.hitEnts.add(ent)
                if not ent.isDead() and ent.team != self.team:
                    info = TakeDamageInfo()
                    info.inflictor = self.shooter
                    info.attacker = self.shooter
                    info.damageType = TFGlobals.DamageType.Burn | TFGlobals.DamageType.PreventPhysicsForce
                    distTraveled = (self.pos - self.srcPos).length()
                    info.setDamage(TFGlobals.remapValClamped(distTraveled, 0, 256, 10, 3))
                    ent.takeDamage(info)
                    ent.burn(self.shooter)
                    #base.world.emitSoundSpatial("Weapon_FlameThrower.FireHit", self.pos)

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
        self.weaponData[TFWeaponMode.Primary].update({
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
        def generate(self):
            TFWeaponGun.generate(self)
            self.pilotLight = Actor()
            self.pilotLight.loadModel("models/weapons/c_flamethrower_pilotlight", False)
            self.pilotLightVM = Actor()
            self.pilotLightVM.loadModel("models/weapons/c_flamethrower_pilotlight", False)

        def disable(self):
            if self.pilotLight:
                self.pilotLight.cleanup()
                self.pilotLight = None
            if self.pilotLightVM:
                self.pilotLightVM.cleanup()
                self.pilotLightVM = None
            TFWeaponGun.disable(self)

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
            self.nextFlameFireTime = globalClock.frame_time + 0.075

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
            TFGlobals.Contents.Solid, 0, TFFilters.TFQueryFilter(self.player))
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
"""SyringeProjectile module: contains the SyringeProjectile class."""

if IS_CLIENT:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from panda3d.core import *

from tf.tfbase import TFFilters, CollisionGroups
from tf.tfbase.TFGlobals import DamageType
from tf.weapon.TakeDamageInfo import TakeDamageInfo, calculateBulletDamageForce, clearMultiDamage, applyMultiDamage

class SyringeProjectile(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        if IS_CLIENT:
            pass
        else:
            self.damage = 0.0
            self.shooter = None
            self.inflictor = None
            self.damage = 100
            self.damageType = DamageType.Bullet

    if not IS_CLIENT:

        def __physSim(self, task):
            dt = globalClock.dt
            accel = Vec3(0, 0, -500)
            oldPos = self.getPos()
            pos = self.getPos() + (self.velocity * dt) + (accel * dt * dt * 0.5)
            self.velocity += accel * dt
            self.lookAt(pos + self.velocity * dt)
            self.setPos(pos)

            filter = TFFilters.TFQueryFilter(self.shooter)
            tr = TFFilters.traceBox(oldPos, pos, Vec3(-8), Vec3(8), CollisionGroups.Mask_BulletCollide, filter)
            if tr['hit']:
                if tr['ent']:
                    if tr['ent'].team != self.team:
                        tr['ent'].traceImpact(tr, {'soundVol': 1.0})
                    dmgInfo = TakeDamageInfo()
                    dmgInfo.inflictor = self.inflictor if self.inflictor else self
                    dmgInfo.attacker = self.shooter
                    dmgInfo.damagePosition = tr['endpos']
                    dmgInfo.sourcePosition = self.shooter.getPos()
                    dmgInfo.setDamage(self.damage)
                    dmgInfo.damageType = self.damageType
                    calculateBulletDamageForce(dmgInfo, self.velocity.normalized(), tr['endpos'], 1.0)
                    clearMultiDamage()
                    tr['ent'].dispatchTraceAttack(dmgInfo, self.velocity.normalized(), tr)
                    applyMultiDamage()
                    #tr['ent'].takeDamage(dmgInfo)
                base.air.deleteObject(self)
                return task.done

            return task.cont

    if IS_CLIENT:
        def onModelChanged(self):
            BaseClass.onModelChanged(self)
            self.modelNp.setP(-90)

    def generate(self):
        BaseClass.generate(self)
        if not IS_CLIENT:
            # Start task to run the physics on the server.
            self.addTask(self.__physSim, "syringePhys", sim=True, appendTask=True)

if not IS_CLIENT:
    SyringeProjectileAI = SyringeProjectile
    SyringeProjectileAI.__name__ = 'SyringeProjectileAI'

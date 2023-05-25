if IS_CLIENT:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase.TFGlobals import DamageType
from tf.weapon.TakeDamageInfo import TakeDamageInfo
from tf.tfbase import TFFilters, Sounds, TFEffects, CollisionGroups, TFGlobals

TF_ROCKET_RADIUS = (110.0 * 1.1)

class BaseRocket(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)

        self.initialVel = Vec3()
        self.critical = False
        if IS_CLIENT:
            self.spawnTime = 0.0
            self.light = None
        else:
            self.exploded = False
            self.ignoreEntity = None
            self.damage = 0.0
            self.collideWithTeammatesTime = 0.0
            self.collideWithTeammates = False
            self.enemy = None
            self.shooter = None
            self.inflictor = None
            self.damage = 100
            self.damageType = DamageType.Blast
            self.sweepGeometry = None

    def determineCollideMask(self):
        """
        Sets the mask of collision groups the rocket should collide with.
        """
        mask = CollisionGroups.World | CollisionGroups.Sky
        if not self.collideWithTeammates:
            # Only collide with the other team.
            mask |= CollisionGroups.Mask_Blue if self.team == TFGlobals.TFTeam.Red else CollisionGroups.Mask_Red
        else:
            # Collide with both teams.
            mask |= CollisionGroups.Mask_AllTeam
        self.intoCollideMask = mask

    if IS_CLIENT:
        def makeTrailsEffect(self, src):
            system = TFEffects.getRocketTrailEffect()
            system.setInput(0, src, False)
            return system

        def __unhideRocket(self, task):
            self.show()
            self.light = qpLight(qpLight.TPoint)
            self.light.setAttenuation(1, 0, 0.001)
            self.light.setAttenuationRadius(256)
            self.light.setColorSrgb(Vec3(1, 0.7, 0.25) * 2)
            self.light.setPos(self.getPos(base.render))
            base.addDynamicLight(self.light, followParent=self)
            self.onUnhideRocket()
            return task.done

        def onUnhideRocket(self):
            pass

        def announceGenerate(self):
            BaseClass.announceGenerate(self)

            return

            # Stick the initial velocity and angles into the interpolation
            # history.
            self.ivPos.clearHistory()
            self.ivRot.clearHistory()

            changeTime = base.clockMgr.getTime()

            # Add a sample one second back.
            currOrigin = self.getPos() - self.initialVel
            self.ivPos.pushFront(currOrigin, changeTime - 1.0, False)
            currRot = self.getQuat()
            self.ivRot.pushFront(currRot, changeTime - 1.0, False)

            # Add the current sample
            currOrigin = self.getPos()
            self.ivPos.pushFront(currOrigin, changeTime, False)
            self.ivRot.pushFront(currRot, changeTime, False)

        def disable(self):
            if self.light:
                base.removeDynamicLight(self.light)
                self.light = None
            BaseClass.disable(self)

    def generate(self):
        BaseClass.generate(self)
        if IS_CLIENT:
            self.spawnTime = base.clockMgr.getTime()

            # Don't render for first 0.2 seconds of being alive.
            self.hide()
            self.addTask(self.__unhideRocket, 'unhideRocket', delay = 0.2, sim = False, appendTask = True)
        else:
            # Don't collide with players on the owner's team for the first bit of life.
            self.collideWithTeammatesTime = base.clockMgr.getTime() + 0.25
            self.collideWithTeammates = False
            self.team = self.shooter.team
            self.determineCollideMask()

            # Build velocity vector from current rotation.
            self.velocity = self.getQuat().getForward()
            self.velocity *= 1100
            self.initialVel = self.velocity

            if not self.sweepGeometry:
                self.sweepGeometry = self.makeModelCollisionShape()[0][1]

            self.addTask(self.__simulateTask, 'RocketSimulateAI', sim=True, appendTask=True)

    if not IS_CLIENT:
        def delete(self):
            self.enemy = None
            self.shooter = None
            self.sweepGeometry = None
            BaseClass.delete(self)

        def explode(self, ent, tr):
            self.exploded = True

            pos = self.getPos()

            # Save this enemy, they will take 100% damage.
            self.enemy = ent
            # Emit explosion from the world at rocket's current position.
            base.world.emitSoundSpatial("BaseExplosionEffect.Sound", pos, chan=Sounds.Channel.CHAN_STATIC)
            base.game.d_doExplosion(pos, Vec3(7), tr['norm'])
            ent.traceDecal('scorch', tr)

            info = TakeDamageInfo()
            info.inflictor = self.inflictor if self.inflictor else self
            info.attacker = self.shooter
            info.damagePosition = pos
            info.sourcePosition = self.shooter.getPos()
            info.damage = self.damage
            info.damageType = self.damageType
            radius = TF_ROCKET_RADIUS
            base.game.radiusDamage(info, pos, radius, -1, self.ignoreEntity)

            # Remove the rocket.
            base.net.deleteObject(self)

        def __simulateTask(self, task):
            self.simulate()
            return task.cont

        def simulate(self):
            BaseClass.simulate(self)

            now = base.clockMgr.getTime()
            if now > self.collideWithTeammatesTime and not self.collideWithTeammates:
                # It's time to collide with teammates.
                self.collideWithTeammates = True
                self.determineCollideMask()

            currPos = self.getPos()
            newPos = currPos + (self.velocity * base.clockMgr.getDeltaTime())

            # Sweep from current pos to new pos.  Check for hits.
            filter = TFFilters.TFQueryFilter(self.shooter)
            tr = TFFilters.traceGeometry(currPos, newPos, self.sweepGeometry, self.intoCollideMask, filter, self.getHpr())
            if tr['hit']:
                if tr['actor']:
                    if tr['actor'].getFromCollideMask() & CollisionGroups.Sky:
                        base.air.deleteObject(self)
                        return
                if tr['ent']:
                    # For some reason endpos is incorrect when using
                    # traceGeometry, so we override it to the intersection
                    # point.
                    tr['endpos'] = tr['pos'] - tr['tracedir'] * 0.1
                    self.setPos(tr['endpos'])
                    self.explode(tr['ent'], tr)

            # Don't do this if we just exploded, because the node has been
            # deleted.
            if not self.exploded:
                self.setPos(newPos)

if not IS_CLIENT:
    BaseRocketAI = BaseRocket
    BaseRocketAI.__name__ = 'BaseRocketAI'

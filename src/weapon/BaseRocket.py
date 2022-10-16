if IS_CLIENT:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase.TFGlobals import Contents, SolidFlag, SolidShape, TakeDamage, DamageType, CollisionGroup
from tf.weapon.TakeDamageInfo import TakeDamageInfo, applyMultiDamage
from tf.tfbase import TFFilters, Sounds, TFEffects

TF_ROCKET_RADIUS = (110.0 * 1.1)

class BaseRocket(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)

        self.initialVel = Vec3()
        self.critical = False
        if IS_CLIENT:
            self.spawnTime = 0.0
        else:
            self.exploded = False
            self.ignoreEntity = None
            self.damage = 0.0
            self.collideWithTeammatesTime = 0.0
            self.collideWithTeammates = False
            self.solidMask = Contents.Solid
            self.collisionGroup = CollisionGroup.Rockets
            self.enemy = None
            self.shooter = None
            self.inflictor = None
            self.damage = 100
            self.damageType = DamageType.Blast
            self.takeDamageMode = TakeDamage.No
            self.sweepGeometry = None

    def determineSolidMask(self):
        contents = Contents.Solid
        if not self.collideWithTeammates:
            # Only collide with the other team.
            contents |= Contents.BlueTeam if self.team == 0 else Contents.RedTeam
        else:
            # Collide with both teams.
            contents |= Contents.AnyTeam
        self.setSolidMask(contents)

    if IS_CLIENT:
        def makeTrailsEffect(self, src):
            system = TFEffects.getRocketTrailEffect()
            system.setInput(0, src, False)
            return system

        def __unhideRocket(self, task):
            self.show()
            return task.done

        def announceGenerate(self):
            BaseClass.announceGenerate(self)

            return

            # Stick the initial velocity and angles into the interpolation
            # history.
            self.ivPos.clearHistory()
            self.ivRot.clearHistory()

            changeTime = globalClock.frame_time

            # Add a sample one second back.
            currOrigin = self.getPos() - self.initialVel
            self.ivPos.pushFront(currOrigin, changeTime - 1.0, False)
            currRot = self.getQuat()
            self.ivRot.pushFront(currRot, changeTime - 1.0, False)

            # Add the current sample
            currOrigin = self.getPos()
            self.ivPos.pushFront(currOrigin, changeTime, False)
            self.ivRot.pushFront(currRot, changeTime, False)


    def generate(self):
        BaseClass.generate(self)
        if IS_CLIENT:
            self.spawnTime = globalClock.frame_time

            # Don't render for first 0.2 seconds of being alive.
            self.hide()
            self.addTask(self.__unhideRocket, 'unhideRocket', delay = 0.2, sim = False, appendTask = True)
        else:
            # Don't collide with players on the owner's team for the first bit of life.
            self.collideWithTeammatesTime = globalClock.frame_time + 0.25
            self.collideWithTeammates = False
            self.team = self.shooter.team
            self.setContentsMask(Contents.Solid | (Contents.RedTeam if self.team == 0 else Contents.BlueTeam))
            self.determineSolidMask()

            # Build velocity vector from current rotation.
            self.velocity = self.getQuat().getForward()
            self.velocity *= 1100
            self.initialVel = self.velocity

            if not self.sweepGeometry:
                self.sweepGeometry = self.makeModelCollisionShape()[0][1]

    if not IS_CLIENT:
        def delete(self):
            self.enemy = None
            self.shooter = None
            self.sweepGeometry = None
            BaseClass.delete(self)

        def explode(self, ent):
            self.exploded = True

            pos = self.getPos()

            # Save this enemy, they will take 100% damage.
            self.enemy = ent
            # Emit explosion from the world at rocket's current position.
            base.world.emitSoundSpatial("BaseExplosionEffect.Sound", pos, chan=Sounds.Channel.CHAN_STATIC)
            base.game.d_doExplosion(pos, Vec3(7))

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

        def simulate(self):
            BaseClass.simulate(self)

            now = globalClock.frame_time
            if now > self.collideWithTeammatesTime and not self.collideWithTeammates:
                # It's time to collide with teammates.
                self.collideWithTeammates = True
                self.determineSolidMask()

            currPos = self.getPos()
            newPos = currPos + (self.velocity * globalClock.dt)

            sweepDir = newPos - currPos
            sweepLen = sweepDir.length()
            sweepDir /= sweepLen

            # Sweep from current pos to new pos.  Check for hits.
            result = PhysSweepResult()
            filter = TFFilters.TFQueryFilter(self.shooter)
            if base.physicsWorld.sweep(result, self.sweepGeometry, currPos, self.getHpr(),
                                       sweepDir, sweepLen, self.solidMask, BitMask32.allOff(),
                                       self.collisionGroup):
                block = result.getBlock()
                actor = block.getActor()
                if actor:
                    np = NodePath(actor)
                    ent = np.getNetPythonTag("entity")
                else:
                    ent = None
                if ent:
                    self.setPos(block.getPosition() - (sweepDir * 0.01))
                    self.explode(ent)

            # Don't do this if we just exploded, because the node has been
            # deleted.
            if not self.exploded:
                self.setPos(newPos)

if not IS_CLIENT:
    BaseRocketAI = BaseRocket
    BaseRocketAI.__name__ = 'BaseRocketAI'

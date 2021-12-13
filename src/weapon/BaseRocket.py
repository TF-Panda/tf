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
from tf.tfbase import TFFilters

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
            self.damage = 0.0
            self.collideWithTeammatesTime = 0.0
            self.collideWithTeammates = False
            self.solidMask = Contents.Solid
            self.collisionGroup = CollisionGroup.Rockets
            #self.solidFlags = SolidFlag.Tangible
            #self.solidShape = SolidShape.Box
            #self.triggerCallback = True
            self.enemy = None
            self.shooter = None
            self.damage = 100
            self.damageType = DamageType.Blast
            self.takeDamageMode = TakeDamage.No
            self.enabled = False
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
        def __unhideRocket(self, task):
            self.show()
            return task.done

        def announceGenerate(self):
            BaseClass.announceGenerate(self)

            # Stick the initial velocity and angles into the interpolation
            # history.
            self.ivPos.clearHistory()
            self.ivRot.clearHistory()

            changeTime = self.getLastChangedTime(self.SimulationVar)

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
            self.spawnTime = globalClock.getFrameTime()

            # Don't render for first 0.2 seconds of being alive.
            self.hide()
            self.addTask(self.__unhideRocket, 'unhideRocket', delay = 0.2, sim = False, appendTask = True)

            self.reparentTo(base.dynRender)
        else:
            # Don't collide with players on the owner's team for the first bit of life.
            self.collideWithTeammatesTime = globalClock.getFrameTime() + 0.25
            self.collideWithTeammates = False
            self.team = self.shooter.team
            self.setContentsMask(Contents.Solid | (Contents.RedTeam if self.team == 0 else Contents.BlueTeam))
            self.determineSolidMask()

            #print("Create rocket at tick", base.tickCount)

            #print("Start rocket at", self.getPos(), self.getHpr())

            # Build velocity vector from current rotation.
            self.velocity = self.getQuat().getForward()
            self.velocity *= 1100
            self.initialVel = self.velocity

            self.sweepGeometry = self.makeModelCollisionShape()[1]

            #print("Vel is", self.velocity)

    if not IS_CLIENT:
        def delete(self):
            self.enemy = None
            self.shooter = None
            self.sweepGeometry = None
            BaseClass.delete(self)

        def explode(self, ent):
            #print("Rocket explode")
            self.exploded = True

            # Save this enemy, they will take 100% damage.
            self.enemy = ent
            self.emitSound("BaseExplosionEffect.Sound")
            base.game.d_doExplosion(self.getPos(), Vec3(7))

            #print("pos", self.getPos())

            info = TakeDamageInfo()
            info.inflictor = self
            info.attacker = self.shooter
            info.damagePosition = self.getPos()
            info.sourcePosition = self.shooter.getPos()
            info.damage = self.damage
            info.damageType = self.damageType
            radius = TF_ROCKET_RADIUS
            base.game.radiusDamage(info, self.getPos(), radius, -1, None)

            # Remove the rocket.
            base.net.deleteObject(self)

        def simulate(self):
            BaseClass.simulate(self)

            now = globalClock.getFrameTime()
            if now > self.collideWithTeammatesTime and not self.collideWithTeammates:
                # It's time to collide with teammates.
                self.collideWithTeammates = True
                self.determineSolidMask()

            currPos = self.getPos()
            newPos = currPos + (self.velocity * globalClock.getDt())

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
                np = NodePath(block.getActor())
                ent = np.getNetPythonTag("entity")
                if ent:
                    self.explode(ent)

            self.setPos(newPos)

            self.enabled = True

if not IS_CLIENT:
    BaseRocketAI = BaseRocket
    BaseRocketAI.__name__ = 'BaseRocketAI'

"""DPipeBombProjectile module: contains the DPipeBombProjectile class."""

# Demoman pipe bomb.
#
# Simulated physics body with a dedicated hull for direct-hit testing.
# Direct-hit testing turns off once the pipe hits a non player or building.

if IS_CLIENT:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from panda3d.core import NodePath, Vec3, Point3
from panda3d.pphysics import PhysSweepResult

from tf.tfbase import TFGlobals, TFFilters, Sounds
from tf.weapon.TakeDamageInfo import TakeDamageInfo

PIPE_DMG_RADIUS = 146
# Damage is reduced by 40% if the pipebomb detonates on timeout instead of
# with a direct hit to an enemy or building.
TIMEOUT_DAMAGE_REDUCTION = 0.6

class DPipeBombProjectile(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)

        if not IS_CLIENT:
            self.damage = 0.0
            self.fullDamage = 0.0
            self.damageType = TFGlobals.DamageType.Blast
            self.shooter = None
            self.takeDamageMode = TFGlobals.TakeDamage.No
            self.solidFlags = TFGlobals.SolidFlag.Tangible
            self.solidShape = TFGlobals.SolidShape.Model
            self.solidMask = TFGlobals.Contents.Solid
            self.collisionGroup = TFGlobals.CollisionGroup.Projectile
            self.kinematic = False
            self.directHull = Vec3(2)
            self.otherTeamMask = 0
            self.contactCallback = True
            self.doingDirectTest = True
            self.enemy = None

    if not IS_CLIENT:
        def generate(self):
            BaseClass.generate(self)
            # This task will test for a direct hit every sim tick until it
            # hits something or the physics body collides with a surface.
            self.addTask(self.__directHitTest, self.uniqueName('directHitTest'), appendTask=True)
            self.addTask(self.__explodeTask, self.uniqueName('explodeTask'), appendTask=True, delay=2.3)
            if self.team == 0:
                self.otherTeamMask = TFGlobals.Contents.BlueTeam
            else:
                self.otherTeamMask = TFGlobals.Contents.RedTeam

        def __explodeTask(self, task):
            self.explode(None)
            return task.done

        def explode(self, ent):
            pos = self.getPos()

            base.world.emitSoundSpatial("Weapon_Grenade_Pipebomb.Explode", pos, chan=Sounds.Channel.CHAN_STATIC)
            base.game.d_doExplosion(pos, Vec3(7))

            self.removeTask(self.uniqueName('explodeTask'))
            self.removeTask(self.uniqueName('directHitTask'))

            self.enemy = ent

            info = TakeDamageInfo()
            info.inflictor = self
            info.attacker = self.shooter
            info.damagePosition = pos
            info.sourcePosition = self.shooter.getPos()
            info.damage = self.damage
            info.damageType = self.damageType
            base.game.radiusDamage(info, pos, PIPE_DMG_RADIUS, -1, None)

            base.air.deleteObject(self)

        def onContactStart(self, entity, actor, pair, shape):
            if actor.getContentsMask() & TFGlobals.Contents.Sky:
                base.air.deleteObject(self)
                return

            if self.doingDirectTest:
                self.removeTask(self.uniqueName('directHitTest'))
                self.doingDirectTest = False

        def __directHitTest(self, task):
            """
            Sweeps ahead using the physics body's currently velocity to see if
            we come in contact with a player or building.  This test is
            disabled when the physics body collides with something.
            """

            currVel = self.node().getLinearVelocity()
            if currVel.length() == 0:
                return task.cont

            currPos = self.getPos(base.render)
            predictedPos = currPos + (currVel * globalClock.dt)
            testDir = predictedPos - currPos
            testDirLen = testDir.length()
            testDir /= testDirLen

            result = PhysSweepResult()
            filter = TFFilters.TFQueryFilter(self)
            if base.physicsWorld.boxcast(result,
                                         currPos - self.directHull,
                                         currPos + self.directHull,
                                         testDir, testDirLen,
                                         Vec3(0),
                                         self.otherTeamMask,
                                         TFGlobals.Contents.Empty,
                                         TFGlobals.CollisionGroup.Empty,
                                         filter):
                block = result.getBlock()
                actor = block.getActor()
                if actor:
                    ent = actor.getPythonTag("entity")
                else:
                    ent = None
                if ent and ent != self.shooter:
                    # Switch to the direct-hit damage.
                    self.damage = self.fullDamage
                    self.explode(ent)
                    return task.done

            return task.cont
    else:
        def announceGenerate(self):
            BaseClass.announceGenerate(self)
            self.skin = self.team
            self.setModel("models/weapons/w_grenade_grenadelauncher")
            # Hide the pipe bomb for the first 0.1 seconds of its life to hide
            # interpolation artifacts.  Same thing is done with rocket
            # projectiles.
            self.hide()
            self.addTask(self.__showTask, self.uniqueName('showPipeBomb'), appendTask=True, delay=0.1)

        #def RecvProxy_pos(self, x, y, z):
        #    BaseClass.RecvProxy_pos(self, x, y, z)
        #    print("Received pos for pipebomb", x, y, z)

        def __showTask(self, task):
            self.show()
            return task.done

if not IS_CLIENT:
    DPipeBombProjectileAI = DPipeBombProjectile
    DPipeBombProjectileAI.__name__ = 'DPipeBombProjectileAI'

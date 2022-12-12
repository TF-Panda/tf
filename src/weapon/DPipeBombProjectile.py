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

from tf.tfbase import TFGlobals, TFFilters, Sounds, TFEffects, CollisionGroups
from tf.weapon.TakeDamageInfo import TakeDamageInfo

PIPE_DMG_RADIUS = 146
# Damage is reduced by 40% if the pipebomb detonates on timeout instead of
# with a direct hit to an enemy or building.
TIMEOUT_DAMAGE_REDUCTION = 0.6

class DPipeBombProjectile(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)

        self.fromCollideMask = CollisionGroups.Projectile
        self.intoCollideMask = CollisionGroups.World | CollisionGroups.Sky

        if not IS_CLIENT:
            self.damage = 0.0
            self.fullDamage = 0.0
            self.damageType = TFGlobals.DamageType.Blast
            self.shooter = None
            self.takeDamageMode = TFGlobals.TakeDamage.No
            self.solidFlags = TFGlobals.SolidFlag.Tangible
            self.solidShape = TFGlobals.SolidShape.Model
            self.kinematic = False
            self.directHull = Vec3(2)
            self.otherTeamMask = 0
            self.contactCallback = True
            self.doingDirectTest = True
            self.enemy = None
        else:
            self.trailEffect = None
            self.timerEffect = None

    if not IS_CLIENT:
        def generate(self):
            BaseClass.generate(self)
            # This task will test for a direct hit every sim tick until it
            # hits something or the physics body collides with a surface.
            self.addTask(self.__directHitTest, self.uniqueName('directHitTest'), appendTask=True)
            self.addTask(self.__explodeTask, self.uniqueName('explodeTask'), appendTask=True, delay=2.3)
            if self.team == TFGlobals.TFTeam.Red:
                self.otherTeamMask = CollisionGroups.Mask_Blue
            else:
                self.otherTeamMask = CollisionGroups.Mask_Red

        def __explodeTask(self, task):
            self.explode(None)
            return task.done

        def explode(self, ent):
            pos = self.getPos()

            base.world.emitSoundSpatial("Weapon_Grenade_Pipebomb.Explode", pos, chan=Sounds.Channel.CHAN_STATIC)

            self.removeTask(self.uniqueName('explodeTask'))
            self.removeTask(self.uniqueName('directHitTask'))

            self.enemy = ent

            explNorm = self.node().getLinearVelocity().normalized()

            if not ent:
                # Trace for scorch mark.
                tr = TFFilters.traceLine(pos + (0, 0, 8), pos - (0, 0, 32), CollisionGroups.World,
                                        TFFilters.TFQueryFilter(self, [TFFilters.worldOnly]))
                if tr['hit'] and tr['ent']:
                    tr['ent'].traceDecal('scorch', tr)
                    explNorm = tr['norm']

            base.game.d_doExplosion(pos, Vec3(7), explNorm)

            info = TakeDamageInfo()
            info.inflictor = self
            info.attacker = self.shooter
            info.damagePosition = pos
            info.sourcePosition = self.shooter.getPos()
            info.damage = self.damage
            info.damageType = self.damageType
            base.game.radiusDamage(info, pos, PIPE_DMG_RADIUS, -1, None)

            if not ent:
                # Only shake screens if it wasn't a direct hit.
                base.game.doScreenShake(pos, 10, 150.0, 1.0, 300.0, 0, True)

            base.air.deleteObject(self)

        def onContactStart(self, entity, actor, pair, shape):
            if actor.getFromCollideMask() & CollisionGroups.Sky:
                base.air.deleteObject(self)
                return

            print("contact start w/", entity, actor)

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

            tr = TFFilters.traceBox(currPos, predictedPos, -self.directHull, self.directHull,
                                    self.otherTeamMask, TFFilters.TFQueryFilter(self))
            if tr['hit']:
                ent = tr['ent']
                if ent and ent != self.shooter:
                    # Switch to the direct-hit damage.
                    self.damage = self.fullDamage
                    self.setPos(tr['endpos'])
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
            self.trailEffect = TFEffects.getPipebombTrailEffect(self.team)
            self.trailEffect.setInput(0, self, False)
            self.trailEffect.start(base.dynRender)
            self.timerEffect = TFEffects.getPipebombTimerEffect(self.team)
            self.timerEffect.setInput(0, self, False)
            self.timerEffect.start(base.dynRender)

        def disable(self):
            if self.trailEffect:
                self.trailEffect.softStop()
                self.trailEffect = None
            if self.timerEffect:
                self.timerEffect.softStop()
                self.timerEffect = None
            BaseClass.disable(self)

        #def RecvProxy_pos(self, x, y, z):
        #    BaseClass.RecvProxy_pos(self, x, y, z)
        #    print("Received pos for pipebomb", x, y, z)

        def __showTask(self, task):
            self.show()
            return task.done

if not IS_CLIENT:
    DPipeBombProjectileAI = DPipeBombProjectile
    DPipeBombProjectileAI.__name__ = 'DPipeBombProjectileAI'

"""DistributedStickyBomb module: contains the DistributedStickyBomb class."""

if IS_CLIENT:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from panda3d.core import *

if not IS_CLIENT:
    from tf.entity.DistributedPropDynamic import DistributedPropDynamicAI
    from tf.entity.World import WorldAI
from tf.tfbase import CollisionGroups, Sounds, TFEffects, TFFilters, TFGlobals
from tf.weapon.TakeDamageInfo import TakeDamageInfo


class DistributedStickyBomb(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        self.takeDamageMode = TFGlobals.TakeDamage.Yes
        self.fromCollideMask = CollisionGroups.Projectile
        self.intoCollideMask = CollisionGroups.World | CollisionGroups.Sky

        self.detTime = 0.0

        if not IS_CLIENT:
            self.solidFlags = TFGlobals.SolidFlag.Tangible
            self.solidShape = TFGlobals.SolidShape.Model
            self.kinematic = False
            self.contactCallback = True
            self.isSticking = False
            self.enemy = None
            self.detonating = False
            self.stickTime = 0.0
            self.numStickContacts = 0
            self.hitSky = False
            self.stickSurfaceNormal = Vec3.forward()
        else:
            self.trailEffect = None
            self.pulseEffect = None

    if not IS_CLIENT:
        def generate(self):
            BaseClass.generate(self)
            self.detTime = base.clockMgr.getTime() + 0.8
            # Don't collide with teammates for the first bit of life.
            # This works around an issue where the sticky bomb gets shoved by
            # the player that shot the sticky.
            self.addTask(self.__collideWithPlayersTask, 'stickyCollideWithPlayers', appendTask=True, sim=True, delay=0.25)

            # Always collide with enemies from the get-go, but don't collide with teammates
            # until later.
            if self.team == TFGlobals.TFTeam.Red:
                otherMask = CollisionGroups.Mask_Blue
            else:
                otherMask = CollisionGroups.Mask_Red
            self.setIntoCollideMask(self.intoCollideMask | otherMask)

            self.addTask(self.__stickTask, 'stickTask', appendTask=True, sim=True, sort=51)

        def __collideWithPlayersTask(self, task):
            # Add players and buildings onto the sticky's into mask.
            self.setIntoCollideMask(self.intoCollideMask | CollisionGroups.Mask_AllTeam)
            return task.done

        #def __stickTask(self, task):

        #    return task.cont

        def onTakeDamage(self, info):
            if self.detonating:
                return

            if not base.game.playerCanTakeDamage(self, info.inflictor):
                return

            if info.damageType & TFGlobals.DamageType.Blast:
                # If we took blast damage, push the sticky.
                # Turn it back into a kinematic object, and stick again after 1 second.
                self.unstick()
                self.stickTime = base.clockMgr.getTime() + 1.0

                BaseClass.onTakeDamage(self, info)

            elif not (info.damageType & TFGlobals.DamageType.Burn):
                # Otherwise destroy the sticky if it was shot with a bullet
                # or hit with a melee.
                self.destroy()

        def destroy(self):
            if self.detonating:
                return
            self.sendUpdate('gib')
            base.air.deleteObject(self)

        def canStickTo(self, entity):
            # Stickies can stick to the world and dynamic props only.
            return isinstance(entity, (WorldAI, DistributedPropDynamicAI))

        def onContactStart(self, entity, actor, pair, shape):
            if actor.getFromCollideMask() & CollisionGroups.Sky:
                # Note that we hit the sky.  Our update task
                # (outside of the physics step) will see the flag
                # and disintegrate the bomb.
                self.hitSky = True
                return

            if entity and self.canStickTo(entity):
                self.stickSurfaceNormal = pair.getContactPoint(0).getNormal()
                self.numStickContacts += 1

        def onContactEnd(self, entity, pair, shape):
            if entity and self.canStickTo(entity):
                self.numStickContacts -= 1

        def unstick(self):
            if self.isSticking:
                self.isSticking = False
                self.setKinematic(False)
                self.node().setCcdEnabled(True)

        def stick(self):
            if not self.isSticking and self.numStickContacts > 0:
                self.setKinematic(True)
                self.isSticking = True

        def __stickTask(self, task):
            if self.hitSky:
                # The bomb hit the sky, so disintegrate.
                base.air.deleteObject(self)
                return task.done

            if self.isSticking:
                return task.cont

            if base.clockMgr.getTime() < self.stickTime:
                return task.cont

            self.stick()

            return task.cont

        def beginDetonate(self):
            assert not self.detonating
            if base.clockMgr.getTime() < self.detTime:
                return False
            self.detonating = True
            return True

        def doDetSound(self, pos=None, volume=None):
            if not pos:
                pos = self.getPos()
            base.world.emitSoundSpatial("Weapon_StickyBombLauncher.ModeSwitch", pos, chan=Sounds.Channel.CHAN_AUTO, volume=volume)
            base.world.emitSoundSpatial("Weapon_Grenade_Pipebomb.Explode", pos, chan=Sounds.Channel.CHAN_AUTO, volume=volume)

        def detonate(self, force, playSound=False):
            assert self.detonating or force

            self.detonating = True

            # Time to detonate.
            pos = self.getPos()
            if playSound:
                self.doDetSound(pos)

            # Trace for scorch mark.
            norm = Vec3.up()
            if self.isSticking:
                norm = self.stickSurfaceNormal
            tr = TFFilters.traceLine(pos + norm * 8, pos - norm * 32, CollisionGroups.World,
                                    TFFilters.TFQueryFilter(self, [TFFilters.worldOnly]))
            if tr['hit'] and tr['ent']:
                tr['ent'].traceDecal('scorch', tr)

            base.game.d_doExplosion(pos, Vec3(7), norm)

            info = TakeDamageInfo()
            info.inflictor = self
            info.attacker = self.shooter
            info.damagePosition = pos
            info.sourcePosition = self.shooter.getPos()
            info.damage = self.damage
            info.damageType = self.damageType
            base.game.radiusDamage(info, pos, 146, -1, None)

            base.game.doScreenShake(pos, 10, 150.0, 1.0, 300.0, 0, True)

            base.air.deleteObject(self)

            return pos

        def delete(self):
            assert self.shooter
            self.shooter.removeDetonateable(self)
            BaseClass.delete(self)

    else:
        def announceGenerate(self):
            BaseClass.announceGenerate(self)
            # Hide the pipe bomb for the first 0.1 seconds of its life to hide
            # interpolation artifacts.  Same thing is done with rocket
            # projectiles.
            self.hide()
            self.addTask(self.__showTask, 'showPipeBomb', appendTask=True, delay=0.1)

            if self.detTime > base.clockMgr.getTime():
                self.addTask(self.__detPulseTask, 'stickyBombDetPulse', appendTask=True, sim=True, delay=(self.detTime - base.clockMgr.getTime()))

            self.trailEffect = TFEffects.getPipebombTrailEffect(self.team)
            self.trailEffect.setInput(0, self, False)
            self.trailEffect.start(base.dynRender)

            self.pulseEffect = TFEffects.getStickybombPulseEffect(self.team)
            self.pulseEffect.setInput(0, self, False)

        def disable(self):
            if self.pulseEffect:
                self.pulseEffect.softStop()
                self.pulseEffect = None
            if self.trailEffect:
                self.trailEffect.softStop()
                self.trailEffect = None
            BaseClass.disable(self)

        def __detPulseTask(self, task):
            self.pulseEffect.start(base.dynRender)
            return task.done

        def gib(self):
            # Become gibs.
            cdata = self.modelData
            if cdata and cdata.hasAttribute("gibs"):
                gibInfo = cdata.getAttributeValue("gibs").getList()
                if gibInfo:
                    from tf.player.PlayerGibs import PlayerGibs
                    PlayerGibs(self.getPos(base.render), self.getHpr(base.render), self.skin, gibInfo, 0.5)
                    self.hide()

        def __showTask(self, task):
            self.show()
            return task.done

if not IS_CLIENT:
    DistributedStickyBombAI = DistributedStickyBomb
    DistributedStickyBombAI.__name__ = 'DistributedStickyBombAI'

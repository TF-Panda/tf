"""DistributedStickyBomb module: contains the DistributedStickyBomb class."""

if IS_CLIENT:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from tf.tfbase import TFGlobals, TFFilters, Sounds
from tf.weapon.TakeDamageInfo import TakeDamageInfo

from panda3d.core import *

class DistributedStickyBomb(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        self.takeDamageMode = TFGlobals.TakeDamage.Yes

        if not IS_CLIENT:
            self.solidFlags = TFGlobals.SolidFlag.Tangible
            self.solidShape = TFGlobals.SolidShape.Model
            self.solidMask = TFGlobals.Contents.Solid
            #self.collisionGroup = TFGlobals.CollisionGroup.Projectile
            self.kinematic = False
            self.contactCallback = True
            self.isSticking = False
            self.enemy = None
            self.detonating = False
            self.stickTime = 0.0
            self.numStickContacts = 0
            self.hitSky = False

    if not IS_CLIENT:
        def generate(self):
            BaseClass.generate(self)
            self.detTime = globalClock.frame_time + 0.8
            self.setContentsMask(TFGlobals.Contents.RedTeam if self.team == TFGlobals.TFTeam.Red else TFGlobals.Contents.BlueTeam)

            self.addTask(self.__stickTask, 'stickTask', appendTask=True, sim=True, sort=51)

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
                self.stickTime = globalClock.frame_time + 1.0

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
            from tf.distributed.World import WorldAI
            from tf.entity.DistributedPropDynamic import DistributedPropDynamicAI
            # Stickies can stick to the world and dynamic props only.
            return isinstance(entity, (WorldAI, DistributedPropDynamicAI))

        def onContactStart(self, entity, actor, pair, shape):
            if actor.getContentsMask() & TFGlobals.Contents.Sky:
                # Note that we hit the sky.  Our update task
                # (outside of the physics step) will see the flag
                # and disintegrate the bomb.
                self.hitSky = True
                return

            if entity and self.canStickTo(entity):
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

            if globalClock.frame_time < self.stickTime:
                return task.cont

            self.stick()

            return task.cont

        def beginDetonate(self):
            assert not self.detonating
            if globalClock.frame_time < self.detTime:
                return False
            self.detonating = True
            return True

        def detonate(self, force):
            assert self.detonating or force

            self.detonating = True

            # Time to detonate.
            pos = self.getPos()
            base.world.emitSoundSpatial("Weapon_StickyBombLauncher.ModeSwitch", pos, chan=Sounds.Channel.CHAN_AUTO)
            base.world.emitSoundSpatial("Weapon_Grenade_Pipebomb.Explode", pos, chan=Sounds.Channel.CHAN_AUTO)
            base.game.d_doExplosion(pos, Vec3(7))

            info = TakeDamageInfo()
            info.inflictor = self
            info.attacker = self.shooter
            info.damagePosition = pos
            info.sourcePosition = self.shooter.getPos()
            info.damage = self.damage
            info.damageType = self.damageType
            base.game.radiusDamage(info, pos, 146, -1, None)

            base.air.deleteObject(self)

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

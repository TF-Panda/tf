from panda3d.pphysics import *
from panda3d.core import *

if IS_CLIENT:
    from tf.actor.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.actor.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from .ObjectState import ObjectState
from tf.actor.Activity import Activity
from tf.tfbase.TFGlobals import Contents, SolidShape, SolidFlag, CollisionGroup, TFTeam
from tf.player.TFClass import Class
from tf.tfbase import Sounds

if not IS_CLIENT:
    from tf.weapon.DWeaponDrop import DWeaponDropAI

import math
import random

tf_object_upgrade_per_hit = 25
tf_obj_gib_velocity_min = 100
tf_obj_gib_velocity_max = 450
tf_obj_gib_maxspeed = 800

class BaseObject(BaseClass):

    Models = []

    def __init__(self):
        BaseClass.__init__(self)
        self.builderDoId = -1
        self.modelIndex = -1
        self.objectState = ObjectState.Off
        # Level of building.
        self.level = 1
        self.maxLevel = 3
        self.upgradeMetalRequired = 200
        self.upgradeMetal = 0
        self.startBuildTime = 0.0
        self.finishBuildTime = 0.0
        self.repairerList = {}
        self.solidShape = SolidShape.Box
        self.solidFlags = SolidFlag.Tangible
        self.kinematic = True
        self.metalToDropInGibs = 65
        self.explodeSound = "Building_Sentry.Explode"
        self.repairMultiplier = 1.0

        self.hasSapper = False
        # DoId of the *player* that placed the sapper.
        # Sapper itself is not an entity.
        self.sapperDoId = 0
        # The number of hits the engineer has made against the placed sapper.
        self.sapperHits = 0

    def isObject(self):
        """
        Returns True if this entity is a building, such as a Sentry
        or Dispenser.  Overriden in BaseObject to return True.
        Convenience method to avoid having to check isinstance() or
        __class__.__name__.
        """
        return True

    #def hasSapper(self):
    #    return False

    def isUpgrading(self):
        return self.objectState == ObjectState.Upgrading

    def isBuilding(self):
        return self.objectState == ObjectState.Constructing

    def isActive(self):
        return self.objectState == ObjectState.Active

    def isPlacing(self):
        # TODO: placing
        return False

    def isDisabled(self):
        return self.objectState == ObjectState.Disabled

    def getBuilder(self):
        """
        Returns the DO/entity that built the object.
        """
        if self.builderDoId < 0:
            return None
        return base.net.doId2do.get(self.builderDoId)

    def setCollideMasks(self):
        self.setContentsMask(Contents.RedTeam if self.team == TFTeam.Red else Contents.BlueTeam)
        # TODO: solid to builder
        #if IS_CLIENT and self.isBuiltByLocalAvatar():
        #    self.setSolidMask()

    if not IS_CLIENT:

        def setModelIndex(self, index):
            if index != self.modelIndex:
                self.modelIndex = index
                self.setModel(self.Models[index])

        def placeSapper(self, doId):
            # Place a sapper from player `doId` onto the building.
            if self.hasSapper:
                return

            self.hasSapper = True
            self.sapperDoId = doId
            self.sapperHits = 0
            self.setObjectState(ObjectState.Disabled)

        def onTakeDamage(self, info):
            if self.health <= 0:
                return

            if not base.game.playerCanTakeDamage(self, info.inflictor):
                return

            self.health = max(0, self.health - info.damage)

            if info.inflictor and info.inflictor.isPlayer():
                info.inflictor.onDamagedOther(self, info.damage)
            elif info.attacker and info.attacker.isPlayer():
                info.attacker.onDamagedOther(self, info.damage)

            if self.health <= 0:
                # Died.
                self.onKilled(info)

        def onKilled(self, info):
            if info.inflictor and info.inflictor.isObject():
                killer = info.inflictor.doId
            else:
                killer = info.attacker.doId
            base.net.game.sendUpdate('killEvent', [killer, -1, -1, self.doId])

            self.explode()
            base.net.deleteObject(self)

        def explode(self):
            pos = self.getPos()
            base.world.emitSoundSpatial(self.explodeSound, pos, chan=Sounds.Channel.CHAN_STATIC)
            base.game.d_doExplosion(pos, Vec3(7))
            self.turnIntoGibs()

        def turnIntoGibs(self):
            """
            Turns the building into a set gibs that give metal/ammo.
            """

            data = self.modelData
            if not data:
                return
            if not data.hasAttribute("gibs"):
                return
            gibs = data.getAttributeValue("gibs").getList()
            if not gibs:
                return
            if len(gibs) <= 0:
                return
            metalPerGib = self.metalToDropInGibs // len(gibs)
            metalDropped = 0
            for i in range(len(gibs)):
                gib_data = gibs.get(i).getElement()
                if not gib_data:
                    continue
                model = gib_data.getAttributeValue("model").getString()
                ap = DWeaponDropAI()
                ap.solidShape = SolidShape.Model
                ap.solidFlags |= SolidFlag.Tangible
                ap.collisionGroup = CollisionGroup.Debris
                ap.kinematic = False
                ap.skin = self.team
                ap.setModel(model)
                ap.node().setSleepThreshold(0.25)
                ap.node().setCcdEnabled(True)
                ap.singleUse = True
                ap.packType = "med"
                ap.metalAmount = metalPerGib
                metalDropped += metalPerGib
                if i == (len(gibs) - 1) and (self.metalToDropInGibs > metalDropped):
                    # Give remainder of metal to drop to last gib.
                    ap.metalAmount += self.metalToDropInGibs - metalDropped
                ap.setTransform(self.getTransform())
                ap.setH(ap.getH() - 180)

                # Calculate the initial impulse on the gib.
                impulse = Vec3(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                impulse.normalize()
                impulse *= random.uniform(tf_obj_gib_velocity_min, tf_obj_gib_velocity_max)
                angImpulse = Vec3(0, random.uniform(-100, -500), 0)

                # Cap the impulse
                speed = impulse.length()
                if speed > tf_obj_gib_maxspeed:
                    impulse *= tf_obj_gib_maxspeed / speed

                #ap.node().setLinearVelocity(impulse)
                #ap.node().setAngularVelocity(angImpulse)
                ap.node().addForce(impulse, ap.node().FTVelocityChange)
                ap.node().addTorque(angImpulse, ap.node().FTVelocityChange)

                base.net.generateObject(ap, self.zoneId)

        def inputWrenchHit(self, player):
            assert player

            didWork = False

            if self.hasSapper:
                pass
            elif self.isUpgrading():
                didWork = False
            elif self.isBuilding():
                self.onRepairHit(player)
                didWork = True
            else:
                didWork = self.onWrenchHit(player)

            return didWork

        def canBeUpgraded(self, player):
            if self.isUpgrading():
                return False

            if player.tfClass != Class.Engineer:
                return False

            if self.level >= self.maxLevel:
                return False

            return True

        def onWrenchHit(self, player):
            amountToHeal = min(100, self.maxHealth - self.health)

            # Repair the building
            repairCost = math.ceil(amountToHeal * 0.2)

            didWork = False

            if repairCost > 0:

                # TODO: take metal away

                if repairCost > player.metal:
                    repairCost = player.metal

                player.metal -= repairCost

                newHealth = min(self.maxHealth, self.health + (repairCost * 5))
                self.health = newHealth

                didWork = repairCost > 0

            # Don't put in upgrade metal until the object is fully healed.
            if not didWork and self.canBeUpgraded(player):
                playerMetal = player.metal
                amountToAdd = min(tf_object_upgrade_per_hit, playerMetal)

                if amountToAdd > (self.upgradeMetalRequired - self.upgradeMetal):
                    amountToAdd = (self.upgradeMetalRequired - self.upgradeMetal)

                player.metal -= amountToAdd

                self.upgradeMetal += amountToAdd

                if amountToAdd > 0:
                    didWork = True

                if self.upgradeMetal >= self.upgradeMetalRequired:
                    self.setObjectState(ObjectState.Upgrading)
                    self.upgradeMetal = 0

            return didWork

        def startUpgrading(self):
            # Increase level.
            self.level += 1
            # More health
            self.maxHealth = int(self.maxHealth * 1.2)
            self.health = self.maxHealth

            self.onUpgrade()

            self.objectState = ObjectState.Upgrading

            # Start the upgrade anim channel.
            self.setAnim(activity = Activity.Object_Upgrade)

        def onUpgrade(self):
            pass

        def onRepairHit(self, player):
            playerId = player.doId
            # The time the repair is going to expire
            repairExpireTime = globalClock.frame_time + 1.0
            # Update or add the expire time to the list
            self.repairerList[playerId] = repairExpireTime

        def getRepairMultiplier(self):
            mult = 1.0

            # Expire all the old
            for playerId in list(self.repairerList.keys()):
                expireTime = self.repairerList[playerId]
                if expireTime < globalClock.frame_time:
                    del self.repairerList[playerId]
                else:
                    # Each player hitting it builds twice as fast.
                    mult += 1.5

            return mult

        def delete(self):
            bldr = self.getBuilder()
            if bldr:
                bldr.removeObject(self.objectType)
            base.game.objectsByTeam[self.team].remove(self)
            BaseClass.delete(self)

        def setBuilderDoId(self, doId):
            self.builderDoId = doId
            bldr = self.getBuilder()
            if not bldr:
                return
            # Be on same team as builder.
            self.team = bldr.team
            base.game.objectsByTeam[self.team].append(self)
            self.setSkin(bldr.team)
            self.setCollideMasks()

        #def getRepairRate(self):
            # TODO
        #    return 1.0

        def setObjectState(self, state):
            self.objectState = state

            if state == ObjectState.Constructing:
                # Start building
                self.setAnim(activity=Activity.Object_Build)
                self.startBuildTime = globalClock.frame_time
                self.onStartConstruction()

            elif state == ObjectState.Upgrading:
                self.startUpgrading()

            elif state == ObjectState.Active:
                self.setAnim(activity=Activity.Object_Idle)
                self.onBecomeActive()

        def onStartConstruction(self):
            pass

        def onFinishConstruction(self):
            pass

        def onBecomeActive(self):
            pass

        def simulateConstructing(self):
            pass

        def simulateActive(self):
            pass

        def simulateDisabled(self):
            pass

        def simulateUpgrading(self):
            pass

        def onFinishUpgrade(self):
            pass

        def generate(self):
            BaseClass.generate(self)

            bldr = self.getBuilder()
            if bldr:
                bldr.setObject(self.objectType, self.doId)

            self.health = 0
            self.hpAccum = 0.0

            self.setObjectState(ObjectState.Constructing)

        def determinePlaybackRate(self):
            if self.isBuilding():
                self.repairMultiplier = self.getRepairMultiplier()
                self.setPlayRate(self.repairMultiplier * 0.5)
            else:
                self.repairMultiplier = 1.0
                self.setPlayRate(1.0)

        def simulate(self):
            BaseClass.simulate(self)

            self.determinePlaybackRate()

            if self.objectState == ObjectState.Constructing:

                hps = self.maxHealth / self.getCurrentAnimLength()
                self.hpAccum += hps * globalClock.dt
                if self.hpAccum >= 1.0:
                    self.health += int(self.hpAccum)
                    self.hpAccum -= int(self.hpAccum)
                self.health = min(self.health, self.maxHealth)

                #self.health = self.maxHealth * self.getCycle()
                if self.isAnimFinished():
                    #self.health = self.maxHealth
                    self.onFinishConstruction()
                    self.setObjectState(ObjectState.Active)
                else:
                    self.simulateConstructing()

            elif self.objectState == ObjectState.Upgrading:
                if self.isAnimFinished():
                    self.onFinishUpgrade()
                    self.setObjectState(ObjectState.Active)
                else:
                    self.simulateUpgrading()

            elif self.objectState == ObjectState.Active:
                self.simulateActive()

            elif self.objectState == ObjectState.Disabled:
                self.simulateDisabled()
    else:
        def onModelChanged(self):
            BaseClass.onModelChanged(self)
            self.updateObjectAnimState()

        def RecvProxy_objectState(self, state):
            if state != self.objectState:
                self.objectState = state
                self.updateObjectAnimState()

        def RecvProxy_repairMultiplier(self, mult):
            self.repairMultiplier = mult
            self.updateObjectPlayRate()

        def updateObjectAnimState(self):
            if self.objectState == ObjectState.Constructing:
                self.setAnim(activity = Activity.Object_Build)
            elif self.objectState == ObjectState.Active:
                self.setAnim(activity = Activity.Object_Idle)
            elif self.objectState == ObjectState.Upgrading:
                self.setAnim(activity = Activity.Object_Upgrade)

            self.updateObjectPlayRate()

        def updateObjectPlayRate(self):
            if self.objectState == ObjectState.Constructing:
                self.setPlayRate(self.repairMultiplier * 0.5)
            else:
                self.setPlayRate(1.0)

        def announceGenerate(self):
            BaseClass.announceGenerate(self)

            self.setSkin(self.team)

            self.setCollideMasks()

            bldr = self.getBuilder()
            if bldr:
                bldr.setObject(self.objectType, self.doId)

            if self.isBuiltByLocalAvatar():
                panel = base.localAvatar.objectPanels.get(self.objectType)
                if panel:
                    panel.setObject(self)

        def delete(self):
            if hasattr(base, 'localAvatar') and self.isBuiltByLocalAvatar():
                panel = base.localAvatar.objectPanels.get(self.objectType)
                if panel:
                    panel.setObject(None)
            bldr = self.getBuilder()
            if bldr:
                bldr.removeObject(self.objectType)
            BaseClass.delete(self)

        def postDataUpdate(self):
            BaseClass.postDataUpdate(self)
            if self.isBuiltByLocalAvatar():
                panel = base.localAvatar.objectPanels.get(self.objectType)
                if panel:
                    panel.updateState()

        def isBuiltByLocalAvatar(self):
            return self.builderDoId == base.localAvatar.doId

if not IS_CLIENT:
    BaseObjectAI = BaseObject
    BaseObjectAI.__name__ = 'BaseObjectAI'

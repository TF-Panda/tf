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
from tf.tfbase.TFGlobals import Contents, SolidShape, SolidFlag, CollisionGroup
from tf.player.TFClass import Class

if not IS_CLIENT:
    from tf.weapon.DWeaponDrop import DWeaponDropAI

import math
import random

tf_object_upgrade_per_hit = 25
tf_obj_gib_velocity_min = 100
tf_obj_gib_velocity_max = 450
tf_obj_gib_maxspeed = 800

class BaseObject(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        self.builderDoId = -1
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
        self.metalToDropInGibs = 65
        self.explodeSound = "Building_Sentry.Explode"

    def hasSapper(self):
        return False

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

    if not IS_CLIENT:

        def onTakeDamage(self, info):
            if self.health <= 0:
                return

            if not base.game.playerCanTakeDamage(self, info.inflictor):
                return

            self.health = max(0, self.health - info.damage)

            if self.health <= 0:
                # Died.
                self.onKilled(info.inflictor)

        def onKilled(self, killer):
            self.explode()
            base.net.deleteObject(self)

        def explode(self):
            self.emitSound(self.explodeSound)
            base.game.d_doExplosion(self.getPos(), Vec3(7))
            self.turnIntoGibs()

        def turnIntoGibs(self):
            """
            Turns the building into a set gibs that give metal/ammo.
            """

            data = self.modelNp.node().getCustomData()
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

                ap.node().addForce(impulse, ap.node().FTImpulse)
                ap.node().addTorque(angImpulse, ap.node().FTImpulse)

                base.net.generateObject(ap, self.zoneId)

        def inputWrenchHit(self, player):
            assert player

            didWork = False

            if self.hasSapper():
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

                newHealth = min(self.maxHealth, self.health + (repairCost * 5))
                self.health = newHealth

                didWork = repairCost > 0

            # Don't put in upgrade metal until the object is fully healed.
            if not didWork and self.canBeUpgraded(player):
                playerMetal = 200 # TODO
                amountToAdd = min(tf_object_upgrade_per_hit, playerMetal)

                if amountToAdd > (self.upgradeMetalRequired - self.upgradeMetal):
                    amountToAdd = (self.upgradeMetalRequired - self.upgradeMetal)

                # TODO: remove metal

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
            self.startChannel(act = Activity.Object_Upgrade)

        def onUpgrade(self):
            pass

        def onRepairHit(self, player):
            playerId = player.doId
            # The time the repair is going to expire
            repairExpireTime = globalClock.getFrameTime() + 1.0
            # Update or add the expire time to the list
            self.repairerList[playerId] = repairExpireTime

        def getRepairMultiplier(self):
            mult = 1.0

            # Expire all the old
            for playerId in list(self.repairerList.keys()):
                expireTime = self.repairerList[playerId]
                if expireTime < globalClock.getFrameTime():
                    del self.repairerList[playerId]
                else:
                    # Each player hitting it builds twice as fast.
                    mult += 1.5

            return mult

        def delete(self):
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
            if self.team == 0:
                self.contentsMask = Contents.RedTeam
            elif self.team == 1:
                self.contentsMask = Contents.BlueTeam

        #def getRepairRate(self):
            # TODO
        #    return 1.0

        def setObjectState(self, state):
            self.objectState = state

            if state == ObjectState.Constructing:
                # Start building
                self.startChannel(act=Activity.Object_Build)
                self.startBuildTime = globalClock.getFrameTime()
                self.onStartConstruction()

            elif state == ObjectState.Upgrading:
                self.startUpgrading()

            elif state == ObjectState.Active:
                self.startChannel(act=Activity.Object_Idle)
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
            self.setObjectState(ObjectState.Constructing)

        def simulate(self):
            BaseClass.simulate(self)

            if self.objectState == ObjectState.Constructing:
                self.setPlayRate(self.getRepairMultiplier() * 0.5)
                self.health = self.maxHealth * self.getCycle()
                if self.isCurrentChannelFinished():
                    self.health = self.maxHealth
                    self.onFinishConstruction()
                    self.setObjectState(ObjectState.Active)
                else:
                    self.simulateConstructing()

            elif self.objectState == ObjectState.Upgrading:
                self.setPlayRate(1.0)
                if self.isCurrentChannelFinished():
                    self.onFinishUpgrade()
                    self.setObjectState(ObjectState.Active)
                else:
                    self.simulateUpgrading()

            elif self.objectState == ObjectState.Active:
                self.setPlayRate(1.0)
                self.simulateActive()
    else:
        def announceGenerate(self):
            BaseClass.announceGenerate(self)

            if self.team == 0:
                self.contentsMask = Contents.RedTeam
            else:
                self.contentsMask = Contents.BlueTeam
            self.node().setContentsMask(self.contentsMask)

            self.reparentTo(base.dynRender)
            if self.isBuiltByLocalAvatar():
                base.localAvatar.objectPanels[self.objectType].setObject(self)

        def delete(self):
            if hasattr(base, 'localAvatar') and self.isBuiltByLocalAvatar():
                base.localAvatar.objectPanels[self.objectType].setObject(None)
            BaseClass.delete(self)

        def postDataUpdate(self):
            BaseClass.postDataUpdate(self)
            if self.isBuiltByLocalAvatar():
                base.localAvatar.objectPanels[self.objectType].updateState()

        def isBuiltByLocalAvatar(self):
            return self.builderDoId == base.localAvatar.doId

if not IS_CLIENT:
    BaseObjectAI = BaseObject
    BaseObjectAI.__name__ = 'BaseObjectAI'

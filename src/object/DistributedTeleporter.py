"""DistributedTeleporter module: contains the DistributedTeleporter class."""

from panda3d.core import *

from .BaseObject import BaseObject
from .ObjectType import ObjectType
from .ObjectState import ObjectState

from tf.tfbase import TFGlobals, TFLocalizer

from direct.interval.IntervalGlobal import *

from direct.directbase import DirectRender

TStateBuilding = 0
TStateIdle = 1
TStateReady = 2
TStateSending = 3
TStateReceiving = 4
TStateReceivingRelease = 5
TStateRecharging = 6

TELEPORTER_RECHARGE_TIME = 10.0

TELEPORTER_FADEOUT_TIME = 0.25
TELEPORTER_FADEIN_TIME = 0.25
TELEPORTER_PLAYER_OFFSET = 20
TELEPORTER_EFFECT_TIME = 12

TELEPORTER_FOV_START = 120
TELEPORTER_FOV_TIME = 0.5

class DistributedTeleporter(BaseObject):
    """
    Base class between entrance and exit.
    """

    Models = [
        "models/buildables/teleporter",
        "models/buildables/teleporter_light",
    ]

    def __init__(self):
        BaseObject.__init__(self)
        # NOTE: Object type set in derived class.

        self.maxHealth = 150

        self.maxLevel = 1
        self.explodeSound = "Building_Teleporter.Explode"

        self.teleState = TStateBuilding
        self.showingBlur = False
        self.showingDirectionArrow = False
        self.yawToExit = 0.0
        self.rechargeTime = 0.0
        self.timesUsed = 0
        self.spinRate = 0.0
        self.rechargeStartTime = 0
        self.rechargeEndTime = 0

        self.viewOffset = Vec3(0, 0, 25)

        if not IS_CLIENT:
            self.solidFlags = TFGlobals.SolidFlag.Tangible | TFGlobals.SolidFlag.Trigger
            # Extend the trigger shape a little bit above the solid hull so
            # the trigger is not blocked by the solid shape.
            self.triggerFudge = Vec3(0, 0, 8)
            self.triggerCallback = True
            self.lastStateChangeTime = 0.0
            self.myNextThink = 0.0

            self.touching = []

            self.teleportingPlayer = None

            # Handle to other side of the teleporter.
            # For an entrance, this is set to the exit, and vice
            # versa for the exit.
            self.other = None

            self.metalToDropInGibs = 25
        else:
            self.spinSound = None
            self.directionPP = None
            self.ivSpinRate = InterpolatedFloat()
            self.addInterpolatedVar(self.ivSpinRate, self.getSpinRate, self.setSpinRate)

    def loadModelBBoxIntoHull(self):
        # Override the collision hull in the model.
        self.hullMins = Point3(-24, -24, 0)
        self.hullMaxs = Point3(24, 24, 12)

    def setCollideMasks(self):
        self.setContentsMask(TFGlobals.Contents.Solid | (TFGlobals.Contents.RedTeam if (self.team == TFGlobals.TFTeam.Red) else TFGlobals.Contents.BlueTeam))
        # This mask determines what can enter the trigger.  Our team only.
        self.setSolidMask(TFGlobals.Contents.RedTeam if (self.team == TFGlobals.TFTeam.Red) else TFGlobals.Contents.BlueTeam)

    def isTeleporterIdle(self):
        return self.teleState == TStateIdle

    def isTeleporterReady(self):
        return self.teleState == TStateReady

    def isTeleporterRecharging(self):
        return self.teleState == TStateRecharging

    def isTeleporterSending(self):
        return self.teleState == TStateSending

    def isTeleporterReceiving(self):
        return self.teleState in (TStateReceiving, TStateReceivingRelease)

    if not IS_CLIENT:

        def onTriggerEnter(self, ent):
            if self.isDODeleted():
                return

            if not ent.isPlayer():
                # Can only teleport players.
                return

            if self.team != ent.team:
                # Not on same team, can't teleport them.
                return

            if ent.isDead():
                # Can't teleport dead players.
                return

            if self.objectType == ObjectType.TeleporterEntrance:
                if not ent in self.touching:
                    self.touching.append(ent)

                #if self.teleState == TStateReady:
                    # If we're an entrance with an exit, we can teleport this
                    # player to the exit.
                #    if ent.velocity.length() < 5.0:
                        # Moving slow enough to assume they are standing on this
                        # teleporter with the intention of using it.
                #        dest = self.other
                #        if dest and not dest.isDODeleted():
                #            self.teleporterSend(ent)

        def onTriggerExit(self, ent):
            if self.isDODeleted():
                return

            if ent in self.touching:
                self.touching.remove(ent)

        def teleporterSend(self, player):
            if not player:
                return

            self.teleportingPlayer = player
            player.setCondition(player.CondSelectedToTeleport)

            self.sendUpdate('teleportEffect', [self.teleportingPlayer.doId])

            self.emitSoundSpatial("Building_Teleporter.Send")

            self.setTeleState(TStateSending)
            self.myNextThink = globalClock.frame_time + 0.1
            self.timesUsed += 1

        def teleporterReceive(self, player, delay):
            if not player:
                return

            self.teleportingPlayer = player

            self.emitSoundSpatial("Building_Teleporter.Receive")

            self.setTeleState(TStateReceiving)
            self.myNextThink = globalClock.frame_time + TELEPORTER_FADEOUT_TIME
            self.timesUsed += 1

        def onKilled(self, info):
            bldr = self.getBuilder()
            if bldr and not bldr.isDead():
                bldr.d_speak("Engineer.AutoDestroyedTeleporter01")
            BaseObject.onKilled(self, info)

        def delete(self):
            # Don't leak reference to other teleporter DO or players.
            self.other = None
            self.teleportingPlayer = None
            self.touching = None
            BaseObject.delete(self)

        def onFinishConstruction(self):
            BaseObject.onFinishConstruction(self)
            self.setModelIndex(1)

        def generate(self):
            self.setModelIndex(0)
            BaseObject.generate(self)

        def setTeleState(self, state):
            if state != self.teleState:
                self.teleState = state
                self.lastStateChangeTime = globalClock.frame_time

        def onBecomeActive(self):
            self.addTask(self.__teleporterThink, "teleporterThink", delay=0.1, appendTask=True)

            self.setTeleState(TStateIdle)

            BaseObject.onBecomeActive(self)

            self.setPlayRate(0.0)
            self.lastStateChangeTime = 0.0

        def findMatch(self):
            if self.objectType == ObjectType.TeleporterEntrance:
                opposite = ObjectType.TeleporterExit
            else:
                opposite = ObjectType.TeleporterEntrance

            bldr = self.getBuilder()
            if not bldr:
                return None

            if bldr.hasObject(opposite):
                obj = base.air.doId2do.get(bldr.objects[opposite])
                if obj and not obj.isDisabled():
                    return obj

            return None

        def isMatchingTeleporterReady(self):
            if self.other is None or self.other.isDODeleted():
                self.other = self.findMatch()

            if self.other and self.other.teleState != TStateBuilding and not self.other.isDisabled():
                return True

            return False

        def showDirectionArrow(self, show):
            if show != self.showingDirectionArrow:
                self.showingDirectionArrow = show

                if show:
                    match = self.other
                    assert match

                    # Compute yaw direction of other teleporter.

                    # Compute vector to other teleporter.
                    toOther = match.getPos(base.render) - self.getPos(base.render)

                    # Look a quat in the direction.
                    q = Quat()
                    lookAt(q, toOther.normalized())

                    # Extract yaw from rotated quat, include our rotation.
                    yaw = q.getHpr().x - self.getH(base.render)

                    self.yawToExit = TFGlobals.angleMod(-yaw + 180)

        def determinePlaybackRate(self):

            playRate = self.getPlayRate()

            wasBelowFullSpeed = (playRate < 1.0)

            if self.isBuilding():
                self.repairMultiplier = self.getRepairMultiplier()
                self.setPlayRate(self.repairMultiplier * 0.5)

            else:
                deltaTime = globalClock.dt

                if self.teleState == TStateReady:
                    # Spin up to 1.0 from whatever we're at, at some high rate.
                    playRate = TFGlobals.approach(1.0, playRate, 0.5 * deltaTime)

                elif self.teleState == TStateRecharging:
                    timeSinceCharge = globalClock.frame_time - self.lastStateChangeTime
                    lowSpinSpeed = 0.15
                    if timeSinceCharge <= 4.0:
                        playRate = TFGlobals.remapVal(globalClock.frame_time,
                            self.lastStateChangeTime,
                            self.lastStateChangeTime + 4.0,
                            1.0,
                            lowSpinSpeed)
                    elif timeSinceCharge > 4.0 and timeSinceCharge <= 6.0:
                        playRate = lowSpinSpeed
                    else:
                        playRate = TFGlobals.remapVal(globalClock.frame_time,
                            self.lastStateChangeTime + 6.0,
                            self.lastStateChangeTime + 10.0,
                            lowSpinSpeed,
                            1.0)
                else:
                    if self.lastStateChangeTime <= 0.0:
                        playRate = 0.0
                    else:
                        # Lost connection to other, spin down to 0.0 slower than
                        # spin up.
                        playRate = TFGlobals.approach(0.0, playRate, 0.25 * deltaTime)

                self.spinRate = playRate

                self.setPlayRate(playRate)

            belowFullSpeed = (playRate < 1.0)
            if belowFullSpeed != wasBelowFullSpeed:
                if belowFullSpeed:
                    self.showingBlur = False
                else:
                    self.showingBlur = True

        def __teleporterThink(self, task):
            if self.isDisabled() or not self.isMatchingTeleporterReady():
                if self.teleState != TStateIdle:
                    self.setTeleState(TStateIdle)
                    self.showDirectionArrow(False)
                return task.again

            if self.myNextThink and self.myNextThink > globalClock.frame_time:
                return task.again

            match = self.other

            if self.teleState == TStateIdle:
                # If our matching teleporter became ready, we are now ready.
                if self.isMatchingTeleporterReady():
                    self.setTeleState(TStateReady)
                    self.emitSoundSpatial("Building_Teleporter.Ready")

                    if self.objectType == ObjectType.TeleporterEntrance:
                        self.showDirectionArrow(True)

            elif self.teleState == TStateReady and self.objectType == ObjectType.TeleporterEntrance:
                # Process touching list, teleport first player that isn't moving.
                for i in range(len(self.touching)):
                    plyr = self.touching[i]
                    if not plyr or plyr.isDODeleted() or plyr.isDead():
                        continue
                    if plyr.velocity.length() < 5.0:
                        # Send them.
                        self.teleporterSend(plyr)
                        break

            elif self.teleState == TStateRecharging:
                now = globalClock.frame_time
                if now > self.rechargeTime:
                    #self.chargePerct = 1.0
                    self.setTeleState(TStateReady)
                    self.emitSoundSpatial("Building_Teleporter.Ready")
                #else:
                #    chargeDuration = self.rechargeTime - self.lastStateChangeTime
                #    rechargeElapsed = now - self.lastStateChangeTime
                #    self.chargePerct = max(0.0, rechargeElapsed / chargeDuration)

            elif self.teleState == TStateSending:
                # Inform exit they are receiving the player we are sending.
                match.teleporterReceive(self.teleportingPlayer, 1.0)
                self.rechargeStartTime = base.tickCount
                match.rechargeStartTime = base.tickCount
                self.rechargeTime = globalClock.frame_time + (TELEPORTER_FADEOUT_TIME + TELEPORTER_FADEIN_TIME + TELEPORTER_RECHARGE_TIME)
                self.rechargeEndTime = base.timeToTicks(self.rechargeTime)
                match.rechargeEndTime = self.rechargeEndTime
                # Start recharging for next teleport.
                self.setTeleState(TStateRecharging)

            elif self.teleState == TStateReceiving:
                # Get the position we'll move the player to.
                newPos = self.getPos(base.render)
                newPos.z += 13.0 # TELEPORTER_MAXS.z + 1.0

                # TODO: telefrag anyone in the way.

                telePlayer = self.teleportingPlayer
                if telePlayer and not telePlayer.isDODeleted():
                    telePlayer.setPos(base.render, newPos)
                    h = self.getH(base.render)
                    telePlayer.setHpr(base.render, h, 0, 0)
                    telePlayer.sendUpdate('doTeleport', [h, 0.5, 120.0])
                    telePlayer.teleport()

                self.setTeleState(TStateReceivingRelease)
                self.myNextThink = globalClock.frame_time + TELEPORTER_FADEIN_TIME

            elif self.teleState == TStateReceivingRelease:
                telePlayer = self.teleportingPlayer
                if telePlayer and not telePlayer.isDODeleted():
                    telePlayer.removeCondition(telePlayer.CondSelectedToTeleport)
                    telePlayer.speakTeleported()

                self.teleportingPlayer = None
                match.teleportingPlayer = None

                self.setTeleState(TStateRecharging)
                self.myNextThink = globalClock.frame_time + TELEPORTER_RECHARGE_TIME

            task.delayTime = 0.05
            return task.again

    else: # IS_CLIENT

        def teleportEffect(self, doId):
            plyr = base.cr.doId2do.get(doId)
            if not plyr:
                return

            from tf.tfbase import TFEffects
            system = TFEffects.getPlayerTeleportEffect(plyr.team)
            system.setInput(0, plyr.modelNp, False)
            # TODO: make the bounce be able to take the plane from an input or something.
            system.addFunction(BounceParticleFunction(LPlane(0, 0, 1, -plyr.getZ()), 0.0))
            system.addFunction(LinearMotionParticleFunction())
            system.addFunction(AngularMotionParticleFunction())
            system.start(base.dynRender)
            Sequence(Wait(0.55), Func(system.softStop)).start()

        def announceGenerate(self):
            BaseObject.announceGenerate(self)
            self.addTask(self.__teleUpdate, "teleUpdateClient", appendTask=True, sim=False)
            self.currBlurAlpha = 0.0

        def disable(self):
            self.directionPP = None
            self.spinSound = None
            self.ivSpinRate = None
            BaseObject.disable(self)

        def setSpinRate(self, rate):
            self.spinRate = rate
            if self.spinSound:
                # Match spin sound play rate to animation play rate.
                self.spinSound.setPlayRate(rate)
            if self.objectState != ObjectState.Constructing:
                self.setPlayRate(rate)

        def getSpinRate(self):
            return self.spinRate

        def __teleUpdate(self, task):
            # Blend in the blur with alpha scale.
            if self.showingBlur:
                if self.currBlurAlpha < 1.0:
                    nodes = self.getBodygroupNodes("teleporter_blur", 1)
                    self.currBlurAlpha = TFGlobals.approach(1.0, self.currBlurAlpha, 1.0 * globalClock.dt)
                    nodes.setColorScale(1, 1, 1, self.currBlurAlpha)

            elif self.currBlurAlpha > 0.0:
                nodes = self.getBodygroupNodes("teleporter_blur", 1)
                self.currBlurAlpha = TFGlobals.approach(0.0, self.currBlurAlpha, 1.0 * globalClock.dt)
                nodes.setColorScale(1, 1, 1, self.currBlurAlpha)

                if self.currBlurAlpha <= 0.0:
                    # Reached 0 alpha, turn off bodygroup.
                    self.setBodygroupValue("teleporter_blur", 0)

            return task.cont

        def startActiveEffects(self):
            if not self.spinSound:
                self.spinSound = self.emitSoundSpatial("Building_Teleporter.SpinLevel1", loop=True)

        def stopActiveEffects(self):
            pass

        def onModelChanged(self):
            BaseObject.onModelChanged(self)

            self.directionPP = self.getPoseParameter("direction")
            if self.directionPP:
                self.directionPP.setValue(self.yawToExit)
            self.setBodygroupValue("teleporter_blur", int(self.showingBlur))
            self.setBodygroupValue("teleporter_direction", int(self.showingDirectionArrow))

            # Don't render blur into shadows.
            for np in self.getBodygroupNodes("teleporter_blur", 1):
                np.hide(DirectRender.ShadowCameraBitmask)

        def RecvProxy_yawToExit(self, yaw):
            self.yawToExit = yaw
            if self.directionPP:
                self.directionPP.setValue(yaw)

        def RecvProxy_showingBlur(self, flag):
            if flag != self.showingBlur:
                if flag:
                    self.setBodygroupValue("teleporter_blur", 1)

                self.showingBlur = flag

        def RecvProxy_showingDirectionArrow(self, flag):
            self.showingDirectionArrow = flag
            self.setBodygroupValue("teleporter_direction", int(self.showingDirectionArrow))

        def RecvProxy_teleState(self, state):
            if state != self.teleState:
                if state > TStateIdle and self.teleState <= TStateIdle:
                    # Went from idle to active.
                    self.startActiveEffects()
                elif state <= TStateIdle and self.teleState > TStateIdle:
                    # Went from active to idle.
                    self.stopActiveEffects()

                self.teleState = state

        def updateObjectPlayRate(self):
            if self.objectState == ObjectState.Active:
                self.setSpinRate(self.spinRate)
            else:
                BaseObject.updateObjectPlayRate(self)

class DistributedTeleporterEntrance(DistributedTeleporter):

    def __init__(self):
        DistributedTeleporter.__init__(self)
        self.objectType = ObjectType.TeleporterEntrance
        self.objectName = TFLocalizer.TeleporterEntrance

class DistributedTeleporterExit(DistributedTeleporter):

    def __init__(self):
        DistributedTeleporter.__init__(self)
        self.objectType = ObjectType.TeleporterExit
        self.objectName = TFLocalizer.TeleporterExit

if not IS_CLIENT:
    DistributedTeleporterAI = DistributedTeleporter
    DistributedTeleporterAI.__name__ = 'DistributedTeleporterAI'
    DistributedTeleporterEntranceAI = DistributedTeleporterEntrance
    DistributedTeleporterEntranceAI.__name__ = 'DistributedTeleporterEntranceAI'
    DistributedTeleporterExitAI = DistributedTeleporterExit
    DistributedTeleporterExitAI.__name__ = 'DistributedTeleporterExitAI'

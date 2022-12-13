""" DistributedTFPlayerOV: Local TF player """

from panda3d.core import WindowProperties, MouseData, Point2, Vec2, Datagram, OmniBoundingVolume, NodePath, Point3, Vec3, lookAt
from panda3d.core import ConfigVariableDouble, InterpolatedVec3, CardMaker, Quat

from panda3d.pphysics import PhysSweepResult, PhysRayCastResult, PhysSphere

from .DistributedTFPlayer import DistributedTFPlayer
from .PlayerCommand import PlayerCommand
from .InputButtons import InputFlag
from .TFClass import *
from .ObserverMode import ObserverMode
from .ScreenShake import ScreenShake
from tf.object.ObjectType import ObjectType

from tf.tfgui.TFHud import TFHud
from tf.tfgui.KillFeed import KillFeed
from tf.tfgui.TFWeaponSelection import TFWeaponSelection
from tf.tfgui import CrossHairInfo
from tf.tfgui.DamageNumbers import DamageNumbers
from tf.tfgui.ChatFeed import ChatFeed
from tf.tfbase import TFGlobals, TFFilters, TFLocalizer, CollisionGroups
from .TFPlayerState import TFPlayerState

from direct.distributed2.ClientConfig import *
from direct.showbase.InputStateGlobal import inputState
from direct.directbase import DirectRender
from direct.gui.DirectGui import *

from tf.tfgui.TFClassMenu import TFClassMenu
from tf.tfgui.TFTeamMenu import TFTeamMenu
from tf.tfgui.VoiceCommandMenu import VoiceCommandMenu

import copy
import random

spec_freeze_time = ConfigVariableDouble("spec-freeze-time", 4.0)
spec_freeze_traveltime = ConfigVariableDouble("spec-freeze-travel-time", 0.4)
spec_freeze_distance_min = ConfigVariableDouble("spec-freeze-distance-min", 96)
spec_freeze_distance_max = ConfigVariableDouble("spec-freeze-distance-max", 200)

mouse_sensitivity = ConfigVariableDouble("mouse-sensitivity", 3.0)
mouse_raw_input = ConfigVariableBool("mouse-raw-input", True)

tf_show_damage_numbers = ConfigVariableBool("tf-show-damage-numbers", False)

# My nvidia so is crashing when I enable relative mode on linux,
# so doing MConfined on linux for now.
#import os
#if os.name == 'nt':
#    mouse_relative = True
#else:
#    mouse_relative = False
mouse_relative = True
print('mouse_relative:', mouse_relative)

WALL_MINS = Vec3(-6)
WALL_MAXS = Vec3(6)

class CommandContext:
    """
    Information about current command being predicted.
    """

    def __init__(self):
        self.needsProcessing = False
        self.cmd = None
        self.commandNumber = 0

class PredictionError:

    def __init__(self):
        self.time = 0.0
        self.error = Vec3()

TF_DEATH_ANIMATION_TIME = 2.0
CHASE_CAM_DISTANCE = 128.0

class DistributedTFPlayerOV(DistributedTFPlayer):

    MaxCommands = 90

    NumNewCmdBits = 4
    MaxNewCommands = ((1 << NumNewCmdBits) - 1)

    NumBackupCmdBits = 3
    MaxBackupCommands = ((1 << NumBackupCmdBits) - 1)

    def __init__(self):
        DistributedTFPlayer.__init__(self)
        self.viewModel = None
        self.commandContext = CommandContext()
        self.commandsSent = 0
        self.lastOutgoingCommand = -1
        self.commandAck = 0
        self.lastCommandAck = 0
        self.chokedCommands = 0
        self.nextCommandTime = 0.0
        self.lastCommand = PlayerCommand()
        self.currentCommand = None
        self.commands = []
        for _ in range(self.MaxCommands):
            self.commands.append(PlayerCommand())
        self.finalPredictedTick = 0
        self.hud = TFHud()
        self.killFeed = KillFeed()
        self.wpnSelect = TFWeaponSelection()
        self.controlsEnabled = False
        self.mouseDelta = Vec2()
        self.classMenu = None
        self.teamMenu = None
        self.crossHairInfo = CrossHairInfo.CrossHairInfo()
        self.dmgNumbers = DamageNumbers()

        self.wasLastWeaponSwitchPressed = False

        self.lastMouseSample = Vec2()

        # Entities that the player predicts/simulates along with itself.  For
        # instance, weapons.
        self.playerSimulatedEntities = []

        self.ivPunchAngle = InterpolatedVec3()
        self.ivPunchAngle.setAngles(True)
        self.addInterpolatedVar(self.ivPunchAngle, self.getPunchAngle, self.setPunchAngle)
        self.ivPunchAngleVel = InterpolatedVec3()
        self.ivPunchAngleVel.setAngles(True)
        self.addInterpolatedVar(self.ivPunchAngleVel, self.getPunchAngleVel, self.setPunchAngleVel)

        self.observerChaseDistance = 0
        self.freezeFrameStart = Point3()
        self.freezeCamStartTime = 0.0
        self.freezeFrameDistance = 0.0
        self.freezeZOffset = 0.0
        self.sentFreezeFrame = False
        self.wasFreezeFraming = False

        self.killedByLabel = None

        self.objectPanels = {}

        self.serverLagCompDebugRoot = None
        self.clientLagCompDebugRoot = None
        self.hitboxDebugRoot = None
        self.clientHitboxDebugRoot = None

        self.respawnTimeLbl = None

        self.nemesisLabels = {}

        self.screenShakes = ScreenShake()

        self.voiceCommandMenus = []
        self.currentVoiceCommandMenu = -1

        self.chatFeed = ChatFeed()

    def doAnimationEvent(self, event, data=0, predicted=True):
        if predicted and base.cr.prediction.inPrediction and not base.cr.prediction.firstTimePredicted:
            return
        self.animState.doAnimationEvent(event, data)

    def createVoiceCommandMenus(self):
        menu1 = VoiceCommandMenu()
        menu1.addItem(TFLocalizer.VoiceCommandMedic, 1, VoiceCommand.Medic)
        menu1.addItem(TFLocalizer.VoiceCommandThanks, 2, VoiceCommand.Thanks)
        menu1.addItem(TFLocalizer.VoiceCommandGoGoGo, 3, VoiceCommand.Go)
        menu1.addItem(TFLocalizer.VoiceCommandMoveUp, 4, VoiceCommand.MoveUp)
        menu1.addItem(TFLocalizer.VoiceCommandGoLeft, 5, VoiceCommand.GoLeft)
        menu1.addItem(TFLocalizer.VoiceCommandGoRight, 6, VoiceCommand.GoRight)
        menu1.addItem(TFLocalizer.VoiceCommandYes, 7, VoiceCommand.Yes)
        menu1.addItem(TFLocalizer.VoiceCommandNo, 8, VoiceCommand.No)
        self.voiceCommandMenus.append(menu1)
        menu2 = VoiceCommandMenu()
        menu2.addItem(TFLocalizer.VoiceCommandIncoming, 1, VoiceCommand.Incoming)
        menu2.addItem(TFLocalizer.VoiceCommandSpy, 2, VoiceCommand.Spy)
        menu2.addItem(TFLocalizer.VoiceCommandSentryAhead, 3, VoiceCommand.SentryAhead)
        menu2.addItem(TFLocalizer.VoiceCommandTeleporterHere, 4, VoiceCommand.TeleporterHere)
        menu2.addItem(TFLocalizer.VoiceCommandDispenserHere, 5, VoiceCommand.DispenserHere)
        menu2.addItem(TFLocalizer.VoiceCommandSentryHere, 6, VoiceCommand.SentryHere)
        menu2.addItem(TFLocalizer.VoiceCommandActivateCharge, 7, VoiceCommand.ActivateCharge)
        menu2.addItem(TFLocalizer.VoiceCommandUberChargeReady, 8, VoiceCommand.ChargeReady)
        self.voiceCommandMenus.append(menu2)
        menu3 = VoiceCommandMenu()
        menu3.addItem(TFLocalizer.VoiceCommandHelp, 1, VoiceCommand.Help)
        menu3.addItem(TFLocalizer.VoiceCommandBattleCry, 2, VoiceCommand.BattleCry)
        menu3.addItem(TFLocalizer.VoiceCommandCheers, 3, VoiceCommand.Cheers)
        menu3.addItem(TFLocalizer.VoiceCommandJeers, 4, VoiceCommand.Jeers)
        menu3.addItem(TFLocalizer.VoiceCommandPositive, 5, VoiceCommand.Positive)
        menu3.addItem(TFLocalizer.VoiceCommandNegative, 6, VoiceCommand.Negative)
        menu3.addItem(TFLocalizer.VoiceCommandNiceShot, 7, VoiceCommand.NiceShot)
        menu3.addItem(TFLocalizer.VoiceCommandGoodJob, 8, VoiceCommand.GoodJob)
        self.voiceCommandMenus.append(menu3)

    def disableCurrentVoiceCommandMenu(self):
        if self.currentVoiceCommandMenu != -1:
            self.voiceCommandMenus[self.currentVoiceCommandMenu].hide()
            self.currentVoiceCommandMenu = -1

    def toggleVoiceCommandMenu(self, index):
        if index == self.currentVoiceCommandMenu:
            self.voiceCommandMenus[index].hide()
            self.currentVoiceCommandMenu = -1
            return

        elif self.currentVoiceCommandMenu != -1:
            self.voiceCommandMenus[self.currentVoiceCommandMenu].hide(False)

        self.voiceCommandMenus[index].show()
        self.currentVoiceCommandMenu = index

    def screenShake(self, cmd, amplitude, freq, duration):
        self.screenShakes.addShake(cmd, amplitude, freq, duration)

    def RecvProxy_numDetonateables(self, count):
        if count != self.numDetonateables:
            self.numDetonateables = count
            messenger.send('localPlayerDetonateablesChanged')

    def isNemesis(self, doId):
        return doId in self.nemesisList

    def RecvProxy_nemesisList(self, nemesisList):
        added = [x for x in nemesisList if x not in self.nemesisList]
        removed = [x for x in self.nemesisList if x not in nemesisList]

        for doId in added:
            self.makeNemesisLabel(doId)
        for doId in removed:
            self.removeNemesisLabel(doId)

        self.nemesisList = nemesisList

    def makeNemesisLabel(self, doId):
        plyr = base.cr.doId2do.get(doId)
        if not plyr:
            return

        tn = TextNode('nemesis')
        tn.setFont(TFGlobals.getTF2BuildFont())
        if plyr.team == TFGlobals.TFTeam.Red:
            tn.setTextColor((0.9, 0.5, 0.5, 1))
        else:
            tn.setTextColor((0.5, 0.65, 1, 1))
        tn.setText(TFLocalizer.NemesisText)
        tn.setAlign(TextNode.ACenter)
        tn.setShadowColor((0.3, 0.3, 0.3, 1))
        tn.setShadow(0.04, 0.04)
        tn.setTextScale(4)
        tnnp = plyr.viewOffsetNode.attachNewNode(tn.generate())
        tnnp.setPos(0, 0, 24)
        tnnp.setBillboardAxis()
        tnnp.setDepthWrite(False)
        self.nemesisLabels[doId] = tnnp

    def removeNemesisLabel(self, doId):
        if doId not in self.nemesisLabels:
            return
        self.nemesisLabels[doId].removeNode()
        del self.nemesisLabels[doId]

    def RecvProxy_observerTarget(self, doId):
        self.observerTarget = doId
        if self.playerState == TFPlayerState.Spectating:
            self.crossHairInfo.setForceEnt(self.observerTarget, CrossHairInfo.CTX_HOVERED)

    def changePlayerState(self, newState, prevState):
        DistributedTFPlayer.changePlayerState(self, newState, prevState)

        if prevState == TFPlayerState.Playing:
            # Hide viewmodel and HUD.
            if self.viewModel:
                self.viewModel.hide()
            self.hud.hideHud()
            self.removeTask('updateCSInfo')
            self.crossHairInfo.clearEnt()
            self.disableCurrentVoiceCommandMenu()
            self.ignore('wheel_up')
            self.ignore('wheel_down')
            self.ignore('x')
            self.ignore('z')
            self.ignore('c')
            self.ignore('e')
            self.ignore('l')

        elif prevState == TFPlayerState.Spectating:
            self.crossHairInfo.clearEnt()
            if self.respawnTimeLbl:
                self.respawnTimeLbl.destroy()
                self.respawnTimeLbl = None
            self.removeTask('respawnTimeLabel')

        if newState == TFPlayerState.Playing:
            self.hide()
            if self.viewModel:
                self.viewModel.show()
            self.hud.showHud()
            self.addTask(self.crossHairInfo.update, 'updateCSInfo', appendTask=True, sim=True)
            self.accept('wheel_up', self.wpnSelect.hoverPrevWeapon)
            self.accept('wheel_down', self.wpnSelect.hoverNextWeapon)
            self.accept('e', self.sendUpdate, ['voiceCommand', [VoiceCommand.Medic]])
            self.accept('z', self.toggleVoiceCommandMenu, [0])
            self.accept('x', self.toggleVoiceCommandMenu, [1])
            self.accept('c', self.toggleVoiceCommandMenu, [2])
            self.accept('l', self.sendUpdate, ['dropFlag'])

        elif newState == TFPlayerState.Spectating:
            self.addTask(self.crossHairInfo.update, 'updateCSInfo', appendTask=True, sim=True)
            if self.observerTarget != -1:
                self.crossHairInfo.setForceEnt(self.observerTarget, CrossHairInfo.CTX_HOVERED)
            if self.respawnTime != 0:
                self.respawnTimeLbl = OnscreenText('', pos=(0, 0.75), fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1), font=TFGlobals.getTF2SecondaryFont())
                self.updateRespawnTimeLbl()
                self.addTask(self.__respawnLabelTask, 'respawnTimeLabel', appendTask=True, sim=True)

    def updateRespawnTimeLbl(self):
        if self.respawnTimeLbl:
            text = TFLocalizer.RespawnIn
            if self.respawnTime < 0:
                text += TFLocalizer.RespawnWaitNewRound
            else:
                timeLeft = int(self.respawnTime - globalClock.frame_time)
                if timeLeft <= 0:
                    text += TFLocalizer.RespawnWait
                else:
                    text += str(timeLeft) + TFLocalizer.RespawnSeconds
            self.respawnTimeLbl.setText(text)

    def __respawnLabelTask(self, task):
        self.updateRespawnTimeLbl()
        return task.cont

    #def disableController(self):
    #    pass

    def onDamagedOther(self, amount, pos):
        if tf_show_damage_numbers.value:
            self.dmgNumbers.addDamage(amount, pos)

    def hitBoxDebug(self, positions, rayStart, rayDirs):
        rayStart = Point3(rayStart[0], rayStart[1], rayStart[2])

        if self.hitboxDebugRoot:
            self.hitboxDebugRoot.removeNode()

        self.hitboxDebugRoot = base.render.attachNewNode('hitboxDebugServer')
        self.hitboxDebugRoot.setRenderModeWireframe()
        self.hitboxDebugRoot.setColor(0, 0, 1, 1)
        self.hitboxDebugRoot.setDepthWrite(False)
        self.hitboxDebugRoot.setDepthTest(False)
        self.hitboxDebugRoot.setBin('fixed', 10000)
        self.hitboxDebugRoot.setTextureOff(1)

        sm = loader.loadModel("models/misc/smiley")
        for pos in positions:
            hbox = sm.copyTo(self.hitboxDebugRoot)
            hbox.setScale(6)
            hbox.setPos(Point3(pos[0], pos[1], pos[2]))

        segs = LineSegs('bulletRaysServer')
        for rayDir in rayDirs:
            rayDir = Vec3(rayDir[0], rayDir[1], rayDir[2])
            segs.moveTo(rayStart)
            segs.drawTo(rayStart + rayDir * 10000)
        self.hitboxDebugRoot.attachNewNode(segs.create())

    def clientHitBoxDebug(self, positions, rayStart, rayDirs):
        rayStart = Point3(rayStart[0], rayStart[1], rayStart[2])

        if self.clientHitboxDebugRoot:
            self.clientHitboxDebugRoot.removeNode()

        self.clientHitboxDebugRoot = base.render.attachNewNode('hitboxDebugClient')
        self.clientHitboxDebugRoot.setRenderModeWireframe()
        self.clientHitboxDebugRoot.setColor(1, 0, 0, 1)
        self.clientHitboxDebugRoot.setDepthWrite(False)
        self.clientHitboxDebugRoot.setDepthTest(False)
        self.clientHitboxDebugRoot.setBin('fixed', 10000)
        self.clientHitboxDebugRoot.setTextureOff(1)

        sm = loader.loadModel("models/misc/smiley")
        for pos in positions:
            hbox = sm.copyTo(self.clientHitboxDebugRoot)
            hbox.setScale(9)
            hbox.setPos(Point3(pos[0], pos[1], pos[2]))

        segs = LineSegs('bulletRaysClient')
        for rayDir in rayDirs:
            rayDir = Vec3(rayDir[0], rayDir[1], rayDir[2])
            segs.moveTo(rayStart)
            segs.drawTo(rayStart + rayDir * 10000)
        self.clientHitboxDebugRoot.attachNewNode(segs.create())

    def lagCompDebug(self, positions):
        if self.serverLagCompDebugRoot:
            self.serverLagCompDebugRoot.removeNode()

        self.serverLagCompDebugRoot = base.render.attachNewNode("serverlagcompdebugroot")
        self.serverLagCompDebugRoot.setDepthWrite(False)
        self.serverLagCompDebugRoot.setDepthTest(False)
        self.serverLagCompDebugRoot.setBin('fixed', 100)
        self.serverLagCompDebugRoot.setColor((0, 0, 1, 1))
        self.serverLagCompDebugRoot.setRenderModeWireframe()
        cm = CardMaker('cm')
        cm.setFrameFullscreenQuad()
        for pos in positions:
            pos = Point3(pos[0], pos[1], pos[2])
            c = self.serverLagCompDebugRoot.attachNewNode(cm.generate())
            c.setBillboardPointEye()
            c.setScale(14)
            c.setPos(pos)

    def clientLagCompDebug(self, positions):
        if base.cr.prediction.inPrediction and not base.cr.prediction.firstTimePredicted:
            return

        if self.clientLagCompDebugRoot:
            self.clientLagCompDebugRoot.removeNode()

        self.clientLagCompDebugRoot = base.render.attachNewNode("clientLagCompDebugRoot")
        self.clientLagCompDebugRoot.setDepthWrite(False)
        self.clientLagCompDebugRoot.setDepthTest(False)
        self.clientLagCompDebugRoot.setBin('fixed', 110)
        self.clientLagCompDebugRoot.setColor((1, 0, 0, 1))
        self.clientLagCompDebugRoot.setRenderModeWireframe()
        cm = CardMaker('cm')
        cm.setFrameFullscreenQuad()
        for pos in positions:
            pos = Point3(pos[0], pos[1], pos[2])
            c = self.clientLagCompDebugRoot.attachNewNode(cm.generate())
            c.setBillboardPointEye()
            c.setScale(16)
            c.setPos(pos)

    def setViewAngles(self, h, p):
        # Server is overriding our current view angles.
        self.viewAngles[0] = h
        self.viewAngles[1] = p
        if self.viewModel:
            self.viewModel.resetSway()

    def setCSHealer(self, doId):
        self.crossHairInfo.setForceEnt(doId, CrossHairInfo.CTX_HEALER)

    def setCSHealTarget(self, doId):
        self.crossHairInfo.setForceEnt(doId, CrossHairInfo.CTX_HEALING)

    def clearCSHealer(self):
        self.crossHairInfo.clearEnt()

    def doTeleport(self, heading, fovDuration, fovStart):
        # Slam exit direction onto view angles heading.
        self.viewAngles[0] = heading

        # Perform the FOV lerp.
        fovStart = fovStart / (4./3.)
        origFov = base.config.GetInt("fov", 75) / (4./3.)
        origVMFov = base.config.GetInt("viewmodel-fov", 54) / (4./3.)

        # Create a flash effect.
        cm = CardMaker('teleFlash')
        cm.setFrameFullscreenQuad()
        cmnp = base.render2d.attachNewNode(cm.generate())
        # Ensure flash quad renders behind all other 2D elements.
        cmnp.setBin('background', -1000)
        cmnp.setTransparency(True)

        r = 1.0
        g = 1.0
        b = 1.0
        cmnp.setColorScale(r, g, b, 0.5)

        from direct.interval.IntervalGlobal import LerpFunc, Sequence, LerpColorScaleInterval, Func, Parallel
        track = Parallel()
        track.append(LerpFunc(base.camLens.setMinFov, fovDuration, fovStart, origFov, blendType='easeOut'))
        track.append(LerpFunc(base.vmLens.setMinFov, fovDuration, fovStart, origVMFov, blendType='easeOut'))
        track.append(
            Sequence(
                LerpColorScaleInterval(cmnp, 0.6, (r, g, b, 0), (r, g, b, 0.5), blendType='easeOut'),
                Func(cmnp.removeNode))
        )
        track.start()

        if self.viewModel:
            self.viewModel.resetSway()

    def shouldSpatializeAnimEventSounds(self):
        return False

    def addPredictionFields(self):
        """
        Called when initializing an entity for prediction.

        This method should define fields that should be predicted
        for this entity.
        """

        DistributedTFPlayer.addPredictionFields(self)

        self.removePredictionField("hpr")

        # Add fields predicted by the local player.
        self.addPredictionField("tickBase", int)
        self.addPredictionField("lastActiveWeapon", int)
        self.addPredictionField("activeWeapon", int, getter=self.getActiveWeapon, setter=self.setActiveWeapon)
        self.addPredictionField("onGround", bool)
        self.addPredictionField("condition", int)
        self.addPredictionField("airDashing", bool, noErrorCheck=True, networked=False)
        self.addPredictionField("buttons", int, noErrorCheck=False, networked=True)
        self.addPredictionField("lastButtons", int, noErrorCheck=False, networked=True)
        self.addPredictionField("buttonsPressed", int, noErrorCheck=True, networked=False)
        self.addPredictionField("buttonsReleased", int, noErrorCheck=True, networked=False)
        self.addPredictionField("stepSoundTime", float, noErrorCheck=True, networked=False)
        self.addPredictionField("punchAngle", Vec3, getter=self.getPunchAngle, setter=self.setPunchAngle, tolerance=0.125)
        self.addPredictionField("punchAngleVel", Vec3, getter=self.getPunchAngleVel, setter=self.setPunchAngleVel, tolerance=0.125)
        # We predict changes to max speed when winding up the heavy's minigun
        # or zooming in with the sniper rifle.
        self.addPredictionField("maxSpeed", float, tolerance=0.5)
        self.addPredictionField("fallVelocity", float, noErrorCheck=True, networked=False)
        self.addPredictionField("fov", float, noErrorCheck=True, networked=False)
        self.addPredictionField("eyeH", float, tolerance=0.01)
        self.addPredictionField("eyeP", float, tolerance=0.01)

    def setActiveWeapon(self, index):
        if self.activeWeapon == index:
            return

        self.lastActiveWeapon = self.activeWeapon
        DistributedTFPlayer.setActiveWeapon(self, index)

    def setObject(self, objectType, doId):
        DistributedTFPlayer.setObject(self, objectType, doId)
        messenger.send('localPlayerObjectsChanged')

    def removeObject(self, objectType):
        DistributedTFPlayer.removeObject(self, objectType)
        messenger.send('localPlayerObjectsChanged')

    def RecvProxy_metal(self, metal):
        if self.metal != metal:
            self.metal = metal
            messenger.send('localPlayerMetalChanged')

    def d_changeClass(self, clsId):
        self.sendUpdate('changeClass', [clsId])
        self.enableControls()
        self.classMenu = None

    def d_changeTeam(self, team):
        self.sendUpdate('changeTeam', [team])
        self.enableControls()
        self.teamMenu = None

    def addPlayerSimulatedEntity(self, ent):
        """
        Adds the indicated entity to the list of entities that are simulated
        by the player.
        """
        if not ent in self.playerSimulatedEntities:
            self.playerSimulatedEntities.append(ent)

    def removePlayerSimulatedEntity(self, ent):
        """
        Removes the indicated entity from the list of entities that are
        simulated by the player.
        """
        if ent in self.playerSimulatedEntities:
            self.playerSimulatedEntities.remove(ent)

    def shouldPredict(self):
        # Local avatar is predicted.
        return True

    def simulate(self):
        # Local player should only be simulated during prediction!
        if not base.net.prediction.inPrediction:
            return

        # Make sure not to simulate this guy twice per frame.
        if self.simulationTick == base.tickCount:
            return

        self.simulationTick = base.tickCount

        ctx = self.commandContext

        if not ctx.needsProcessing:
            # No commmand to process!
            return

        ctx.needsProcessing = False

        base.net.prediction.runCommand(self, ctx.cmd)

    def calcView(self):
        """
        Main routine to calculate position and angles for the camera.
        """

        base.camLens.setMinFov(self.fov / (4./3.))

        if self.playerState == TFPlayerState.Died:
            if self.observerMode == ObserverMode.DeathCam:
                self.calcDeathCamView()
            elif self.observerMode == ObserverMode.FreezeCam:
                self.calcFreezeCamView()
        elif self.playerState == TFPlayerState.Spectating:
            self.calcSpectatorView()
        else:
            self.calcPlayingView()

        # Add shake offset.
        self.screenShakes.calcShake()
        base.cam.setPos(self.screenShakes.shakeAppliedOffset)
        base.cam.setR(-self.screenShakes.shakeAppliedAngle)

    def calcPlayingView(self):
        if self.isLoser() or self.inCondition(self.CondTaunting):
            self.show()
            if self.viewModel:
                self.viewModel.hide()
            self.calcSpectatorView(self, 48*2)
        else:
            self.hide()
            base.camera.setPos(self.getEyePosition())
            base.camera.setHpr(self.viewAngles + self.punchAngle)
            if self.viewModel:
                # Don't render the view model when zoomed.
                if not self.inCondition(self.CondZoomed):
                    self.viewModel.show()
                    # Also calculate the viewmodel position/rotation.
                    self.viewModel.calcView(self, base.camera)
                else:
                    self.viewModel.hide()

    def camBlock(self, camPos, targetPos, camTargetEntity):
        """
        Given a desired camPos, offset a certain distance from targetPos,
        traces a line from targetPos to camPos, and moves camPos in front
        of any obstructions.

        Returns True if there was an obstruction and camPos was moved, False
        otherwise.
        """

        tr = TFFilters.traceSphere(targetPos, camPos, 8.0,
            CollisionGroups.World, TFFilters.TFQueryFilter(camTargetEntity))
        if tr['hit']:
            return (True, tr['endpos'])
        return (False, camPos)

    def calcThirdPersonView(self):
        maxDist = 128
        viewQuat = Quat()
        viewQuat.setHpr(self.viewAngles)
        base.camera.setHpr(self.viewAngles)
        origin = self.getEyePosition()
        vForward = viewQuat.getForward()
        eyeOrigin = Point3(origin + (vForward * -maxDist))

        # Clip against world.
        tr = self.camBlock(eyeOrigin, origin, self)
        if tr[0]:
            eyeOrigin = tr[1]

        base.camera.setPos(eyeOrigin)

    def calcSpectatorView(self, specTarget=None, chaseSpeed=48.0):
        if not specTarget:
            specTarget = base.net.doId2do.get(self.observerTarget)
        if not specTarget:
            return

        self.observerChaseDistance += globalClock.dt * chaseSpeed
        self.observerChaseDistance = max(16, min(CHASE_CAM_DISTANCE, self.observerChaseDistance))

        viewQuat = Quat()
        viewQuat.setHpr(self.viewAngles)
        base.camera.setHpr(self.viewAngles)

        origin = specTarget.getEyePosition()

        if specTarget.isPlayer():
            if (specTarget.deathType == self.DTRagdoll) and specTarget.ragdoll:
                origin = specTarget.ragdoll[1].getRagdollPosition()
                origin.z += 40
            elif (specTarget.deathType == self.DTGibs) and specTarget.gibs and specTarget.gibs.valid:
                origin = specTarget.gibs.getHeadPosition()
                origin.z += 40

        vForward = viewQuat.getForward()
        eyeOrigin = Point3(origin + (vForward * -self.observerChaseDistance))

        # Clip against world.
        tr = self.camBlock(eyeOrigin, origin, specTarget)
        if tr[0]:
            eyeOrigin = tr[1]
            self.observerChaseDistance = (origin - eyeOrigin).length()

        base.camera.setPos(eyeOrigin)

    def calcDeathCamView(self):
        killer = base.net.doId2do.get(self.observerTarget)

        # Swing to face our killer within half the death anim time.
        interpolation = (globalClock.frame_time - self.deathTime) / (TF_DEATH_ANIMATION_TIME * 0.5)
        interpolation = max(0, min(1, interpolation))
        interpolation = TFGlobals.simpleSpline(interpolation)

        self.observerChaseDistance += globalClock.dt * 48.0
        self.observerChaseDistance = max(16, min(CHASE_CAM_DISTANCE, self.observerChaseDistance))

        aForward = self.viewAngles
        qForward = Quat()
        qForward.setHpr(aForward)

        if (self.deathType == self.DTRagdoll) and self.ragdoll:
            origin = self.ragdoll[1].getRagdollPosition()
            origin.z += 40
        elif (self.deathType == self.DTGibs) and self.gibs and self.gibs.valid:
            origin = self.gibs.getHeadPosition()
            origin.z += 40
        else:
            origin = self.getEyePosition()

        if killer and killer != self:
            # Compute angles to look at killer.
            vKiller = killer.getEyePosition() - origin
            qKiller = Quat()
            lookAt(qKiller, vKiller)
            Quat.slerp(qForward, qKiller, interpolation, qForward)

        base.camera.setHpr(qForward.getHpr())

        vForward = qForward.getForward()
        vForward.normalize()
        eyeOrigin = Point3(origin + (vForward * -self.observerChaseDistance))

        # Clip against world.
        tr = self.camBlock(eyeOrigin, origin, killer)
        if tr[0]:
            eyeOrigin = tr[1]
            self.observerChaseDistance = (origin - eyeOrigin).length()

        base.camera.setPos(eyeOrigin)

    def calcFreezeCamView(self):
        curTime = globalClock.frame_time - self.freezeCamStartTime

        target = base.net.doId2do.get(self.observerTarget)
        if not target:
            self.calcDeathCamView()
            return

        # Zoom towards our target.
        blendPerc = max(0, min(1, curTime / spec_freeze_traveltime.getValue()))
        blendPerc = TFGlobals.simpleSpline(blendPerc)

        camDesired = target.getPos()
        if target.isPlayer():
            if (target.deathType == self.DTRagdoll) and target.ragdoll:
                camDesired = target.ragdoll[1].getRagdollPosition()
            elif (target.deathType == self.DTGibs) and target.gibs and target.gibs.valid:
                camDesired = target.gibs.getHeadPosition()
        if target.health > 0:
            camDesired[2] += target.viewOffset[2]
        #else:
        #    camDesired[2] += 40
        camTarget = Point3(camDesired)
        if target.health > 0:
            mins = Vec3()
            maxs = Vec3()
            # Look at their chest, not their head.
            target.calcTightBounds(mins, maxs, base.render)
            camTarget[2] -= (maxs[2] * 0.5)
        else:
            # Look over ragdoll, not through.
            camTarget[2] += 40

        # Figure out a view position in front of the target
        #print("eye on plane", base.camera.getPos())
        eyeOnPlane = base.camera.getPos()
        eyeOnPlane[2] = camTarget[2]
        targetPos = Vec3(camTarget)
        toTarget = targetPos - eyeOnPlane
        toTarget.normalize()

        # Stop a few units away from the target, and shift up to be at the same height
        targetPos = camTarget - (toTarget * self.freezeFrameDistance)
        eyePosZ = target.getZ() + target.viewOffset[2]
        targetPos[2] = eyePosZ + self.freezeZOffset

        # Trace so that we're put in front of any walls.
        tr = self.camBlock(targetPos, camTarget, target)
        if tr[0]:
            # The camera's going to be really close to the target.  So we
            # don't end up looking at someone's chest, aim close freezecams
            # at the target's eyes.
            targetPos = tr[1]
            camTarget = camDesired

            # To stop all close in views looking up at character's chins,
            # move the view up.
            targetPos[2] += abs(camTarget[2] - targetPos[2]) * 0.85

            tr = self.camBlock(targetPos, camTarget, target)
            if tr[0]:
                targetPos = tr[1]

        # Look directly at the target.
        toTarget = camTarget - targetPos
        toTarget.normalize()
        q = Quat()
        lookAt(q, toTarget)
        base.camera.setHpr(q.getHpr())

        base.camera.setPos((self.freezeFrameStart * (1 - blendPerc)) + (targetPos * blendPerc))

        if curTime >= spec_freeze_traveltime.getValue() and not self.sentFreezeFrame:
            # Freeze the frame.
            base.postProcess.freezeFrame.freezeFrame(spec_freeze_time.getValue())
            # Hide the scene.  However, it needs to be done *next* frame, after the freeze
            # frame has been taken, so we add it as a task with a delay of 0, which achieves
            # that.
            base.taskMgr.doMethodLater(0.1, self.__hideSceneFreezeFrame, 'hideSceneFreezeFrame')
            #for mgr in base.sfxManagerList:
            #    mgr.setVolume(0.0)
            if self.killedByLabel:
                self.killedByLabel.destroy()
            if target.isObject():
                builder = target.getBuilder()
                if builder and self.isNemesis(builder.doId):
                    text = TFLocalizer.YouWereKilledByTheNemesis
                else:
                    text = TFLocalizer.YouWereKilledByThe
                if target.isDead():
                    text += TFLocalizer.KillerLate
                text += TFLocalizer.KillerSentryGun
                if builder:
                    if builder.isDead():
                        text += TFLocalizer.KillerTheLate
                    text += builder.playerName
            else:
                if self.isNemesis(target.doId):
                    text = TFLocalizer.YouWereKilledByNemesis
                else:
                    text = TFLocalizer.YouWereKilledBy
                if target.isDead():
                    text += TFLocalizer.KillerTheLate
                text += target.playerName
            text += "!"

            self.killedByLabel = OnscreenText(text = text,
                                              pos = (0, 0.75), fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1),
                                              font = TFGlobals.getTF2SecondaryFont())
            self.sentFreezeFrame = True

    def __hideSceneFreezeFrame(self, task):
        base.render.hide()
        base.sky3DTop.hide()
        base.vmRender.hide()
        return task.done

    def __showSceneFreezeFrame(self):
        base.render.show()
        base.sky3DTop.show()
        base.vmRender.show()

    def onTFClassChanged(self):
        DistributedTFPlayer.onTFClassChanged(self)

        if self.tfClass == Class.Engineer and not self.objectPanels:
            self.createObjectPanels()
        elif self.tfClass != Class.Engineer:
            self.destroyObjectPanels()

    def RecvProxy_weapons(self, weapons):
        changed = weapons != self.weapons
        #print(weapons, self.weapons)
        self.weapons = weapons
        if changed:
            #print("rebuild wpn list")
            self.wpnSelect.rebuildWeaponList()

    def RecvProxy_health(self, hp):
        changed = hp != self.health
        self.health = hp
        if changed:
            self.hud.updateHealthLabel()

    def RecvProxy_maxHealth(self, maxHp):
        changed = maxHp != self.maxHealth
        self.maxHealth = maxHp
        if changed:
            self.hud.updateHealthLabel()

    def getNextCommandNumber(self):
        return self.lastOutgoingCommand + self.chokedCommands + 1

    def getNextCommand(self):
        return self.commands[self.getNextCommandNumber() % self.MaxCommands]

    def shouldSendCommand(self):
        return globalClock.frame_time >= self.nextCommandTime and base.cr.connected

    def getCommand(self, num):
        cmd = self.commands[num % self.MaxCommands]
        if cmd.commandNumber != num:
            return None
        return cmd

    def writeCommandDelta(self, dg, prev, to, isNew):
        nullCmd = PlayerCommand()

        if prev == -1:
            f = nullCmd
        else:
            f = self.getCommand(prev)
            if not f:
                f = nullCmd

        t = self.getCommand(to)

        if not t:
            t = nullCmd

        t.writeDatagram(dg, f)

        return True

    def sendCommand(self):
        nextCommandNum = self.getNextCommandNumber()

        dg = Datagram()

        # Send the player command message.

        cmdBackup = 2
        backupCommands = max(0, min(cmdBackup, self.MaxBackupCommands))
        dg.addUint8(backupCommands)

        newCommands = 1 + self.chokedCommands
        newCommands = max(0, min(newCommands, self.MaxNewCommands))
        dg.addUint8(newCommands)

        numCmds = newCommands + backupCommands

        # First command is delta'd against zeros.
        prev = -1

        ok = True

        firstBackupCommand = nextCommandNum - numCmds
        lastBackupCommand = firstBackupCommand + backupCommands
        firstNewCommand = lastBackupCommand
        lastNewCommand = firstNewCommand + newCommands
        for to in range(firstBackupCommand, lastBackupCommand):
            ok = ok and self.writeCommandDelta(dg, prev, to, False)
            prev = to
        for to in range(firstNewCommand, lastNewCommand):
            ok = ok and self.writeCommandDelta(dg, prev, to, True)
            prev = to

        if ok:
            self.sendUpdate('playerCommand', [dg.getMessage()])
            self.commandsSent += newCommands

    def considerSendCommand(self):
        if self.shouldSendCommand():
            self.sendCommand()
            base.cr.sendTick()

            self.lastOutgoingCommand = self.commandsSent - 1
            self.chokedCommands = 0

            # Determine when to send next command.
            cmdIval = 1.0 / cl_cmdrate.getValue()
            maxDelta = min(base.intervalPerTick, cmdIval)
            delta = max(0.0, min(maxDelta, globalClock.frame_time - self.nextCommandTime))
            self.nextCommandTime = globalClock.frame_time + cmdIval - delta
        else:
            # Not sending yet, but building a list of commands to send.
            self.chokedCommands += 1

    def generate(self):
        DistributedTFPlayer.generate(self)
        base.localAvatar = self
        base.localAvatarId = self.doId

    def delete(self):
        if self.chatFeed:
            self.chatFeed.cleanup()
            self.chatFeed = None
        for menu in self.voiceCommandMenus:
            menu.cleanup()
        self.voiceCommandMenus = None
        if self.nemesisLabels:
            for lbl in self.nemesisLabels.values():
                lbl.removeNode()
            self.nemesisLabels = None
        if self.clientLagCompDebugRoot:
            self.clientLagCompDebugRoot.removeNode()
            self.clientLagCompDebugRoot = None
        if self.serverLagCompDebugRoot:
            self.serverLagCompDebugRoot.removeNode()
            self.serverLagCompDebugRoot = None
        if self.hitboxDebugRoot:
            self.hitboxDebugRoot.removeNode()
            self.hitboxDebugRoot = None
        if self.clientHitboxDebugRoot:
            self.clientHitboxDebugRoot.removeNode()
            self.clientHitboxDebugRoot = None
        self.disableControls()
        if self.dmgNumbers:
            self.dmgNumbers.cleanup()
            self.dmgNumbers = None
        if self.respawnTimeLbl:
            self.respawnTimeLbl.destroy()
            self.respawnTimeLbl = None
        if self.crossHairInfo:
            self.crossHairInfo.destroy()
            self.crossHairInfo = None
        if self.killFeed:
            self.killFeed.cleanup()
            self.killFeed = None
        if self.hud:
            self.hud.destroy()
            self.hud = None
        if self.wpnSelect:
            self.wpnSelect.destroy()
            self.wpnSelect = None
        self.commandContext = None
        self.lastCommand = None
        self.commands = None
        if self.classMenu:
            self.classMenu.destroy()
            self.classMenu = None
        if self.teamMenu:
            self.teamMenu.destroy()
            self.teamMenu = None
        self.playerSimulatedEntities = None
        base.simTaskMgr.remove('runControls')
        base.taskMgr.remove('calcView')
        base.taskMgr.remove('mouseMovement')
        base.taskMgr.remove('hideSceneFreezeFrame')

        del base.localAvatar
        del base.localAvatarId
        DistributedTFPlayer.delete(self)

    def announceGenerate(self):
        DistributedTFPlayer.announceGenerate(self)
        self.hide()

        base.cr.sendTick()

        self.fwd = inputState.watchWithModifiers("forward", "w", inputSource = inputState.WASD)
        self.bck = inputState.watchWithModifiers("backward", "s", inputSource = inputState.WASD)
        self.left = inputState.watchWithModifiers("left", "a", inputSource = inputState.WASD)
        self.right = inputState.watchWithModifiers("right", "d", inputSource = inputState.WASD)
        self.crouch = inputState.watchWithModifiers("crouch", "control", inputSource = inputState.Keyboard)
        self.jump = inputState.watchWithModifiers("jump", "space", inputSource = inputState.Keyboard)
        self.attack1 = inputState.watchWithModifiers("attack1", "mouse1", inputSource = inputState.Mouse)
        self.reload = inputState.watchWithModifiers("reload", "r", inputSource = inputState.Keyboard)
        self.attack2 = inputState.watchWithModifiers("attack2", "mouse3", inputSource = inputState.Mouse)
        self.lastWeapon = inputState.watchWithModifiers("lastweapon", "q", inputSource = inputState.Keyboard)

        self.accept(',', self.doChangeClass)
        self.accept('.', self.doChangeTeam)
        self.accept('i', self.sendUpdate, ['reloadResponses'])
        self.accept('y', self.chatFeed.showChatEntry)

        self.createVoiceCommandMenus()

        base.taskMgr.add(self.mouseMovement, 'mouseMovement')
        base.taskMgr.add(self.calcViewTask, 'calcView', sort = 38)

        self.startControls()

        props = WindowProperties()
        props.setTitle(f"Team Fortress - {self.doId}")
        base.win.requestProperties(props)

        self.accept('escape', self.enableControls)

    def startControls(self):
        base.simTaskMgr.add(self.runControls, 'runControls')

    def stopControls(self):
        base.simTaskMgr.remove('runControls')

    def doChangeClass(self):
        if not base.game.isChangeClassAllowed():
            return

        if self.classMenu:
            return
        if self.teamMenu:
            self.teamMenu.destroy()
            self.teamMenu = None
        self.classMenu = TFClassMenu()
        self.disableControls()

    def doChangeTeam(self):
        if not base.game.isChangeTeamAllowed():
            return

        if self.teamMenu:
            return
        if self.classMenu:
            self.classMenu.destroy()
            self.classMenu = None
        self.teamMenu = TFTeamMenu()
        self.disableControls()

    def createObjectPanels(self):
        from tf.tfgui.ObjectPanel import SentryPanel, DispenserPanel, EntrancePanel, ExitPanel
        self.objectPanels[ObjectType.SentryGun] = SentryPanel()
        self.objectPanels[ObjectType.SentryGun].updateState()
        self.objectPanels[ObjectType.Dispenser] = DispenserPanel()
        self.objectPanels[ObjectType.Dispenser].updateState()
        self.objectPanels[ObjectType.TeleporterEntrance] = EntrancePanel()
        self.objectPanels[ObjectType.TeleporterEntrance].updateState()
        self.objectPanels[ObjectType.TeleporterExit] = ExitPanel()
        self.objectPanels[ObjectType.TeleporterExit].updateState()

    def destroyObjectPanels(self):
        for panel in self.objectPanels.values():
            panel.destroy()
        self.objectPanels = {}

    def calcViewTask(self, task):
        self.calcView()
        return task.cont

    def enableControls(self):
        if self.controlsEnabled:
            return

        base.disableMouse()

        props = WindowProperties()
        props.setCursorHidden(True)
        if mouse_relative:
            props.setMouseMode(WindowProperties.MRelative)
        else:
            props.setMouseMode(WindowProperties.MConfined)

        base.win.requestProperties(props)

        #base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)
        if mouse_relative:
            if base.mouseWatcherNode.hasMouse():
                md = base.mouseWatcherNode.getMouse()
                sizeX = base.win.getXSize()
                sizeY = base.win.getYSize()
                self.lastMouseSample = Vec2((md.getX() * 0.5 + 0.5) * sizeX, (md.getY() * 0.5 + 0.5) * sizeY)
            else:
                self.lastMouseSample = Vec2()
        else:
            base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)
            self.lastMouseSample = Vec2()

        self.mouseDelta = Vec2()

        self.accept('escape', self.disableControls)

        self.controlsEnabled = True

    def mouseMovement(self, task):
        """
        Runs every frame to get smooth mouse movement.  Delta is accumulated
        over multiple frames for player command tick.
        """

        mw = base.mouseWatcherNode

        doMovement = self.controlsEnabled and mw.hasMouse()
        if self.playerState == TFPlayerState.Died and self.observerTarget not in (-1, self.doId):
            doMovement = False

        if doMovement:
            sens = mouse_sensitivity.value
            sens *= self.fov / self.defaultFov
            #if self.inCondition(self.CondZoomed):
            #    sens /= 2
            sizeX = base.win.size.x
            sizeY = base.win.size.y
            if mouse_relative:
                md = mw.getMouse()
                sample = Vec2((md.x * 0.5 + 0.5) * sizeX, (md.y * 0.5 + 0.5) * sizeY)
            else:
                md = base.win.getPointer(0)
                sample = Vec2(md.x, md.y)
                base.win.movePointer(0, sizeX // 2, sizeY // 2)

            delta = (sample - self.lastMouseSample) * sens

            self.viewAngles[0] -= delta.x * 0.022
            self.viewAngles[1] = max(-89, min(89, self.viewAngles[1] + (delta.y * 0.022)))
            self.viewAngles[2] = 0.0
            self.mouseDelta += delta
            self.lastMouseSample = sample
        return task.cont

    def runControls(self, task):
        cmd = self.getNextCommand()
        cmd.clear()
        cmd.commandNumber = self.getNextCommandNumber()
        rand = random.Random(cmd.commandNumber)
        cmd.randomSeed = rand.randint(0, 0xFFFFFFFF)
        cmd.tickCount = base.tickCount

        fastWpnSwitch = base.config.GetBool('tf-fast-weapon-switch', 0)

        cmd.buttons = InputFlag.Empty
        if not self.isDead():
            cmd.viewAngles = Vec3(self.viewAngles)
            cmd.mouseDelta = Vec2(self.mouseDelta)
            if inputState.isSet("forward"):
                cmd.buttons |= InputFlag.MoveForward
            if inputState.isSet("backward"):
                cmd.buttons |= InputFlag.MoveBackward
            if inputState.isSet("left"):
                cmd.buttons |= InputFlag.MoveLeft
            if inputState.isSet("right"):
                cmd.buttons |= InputFlag.MoveRight
            if inputState.isSet("jump"):
                cmd.buttons |= InputFlag.Jump
            if inputState.isSet("crouch"):
                cmd.buttons |= InputFlag.Crouch
            if inputState.isSet("attack1"):
                if self.wpnSelect.isActive and not fastWpnSwitch:
                    cmd.weaponSelect = self.wpnSelect.index
                    self.wpnSelect.hide()
                else:
                    cmd.buttons |= InputFlag.Attack1

            if fastWpnSwitch and self.wpnSelect.isActive:
                cmd.weaponSelect = self.wpnSelect.index
                self.wpnSelect.hide()

            if inputState.isSet("lastweapon"):
                if not self.wasLastWeaponSwitchPressed:
                    if self.lastActiveWeapon >= 0 and self.lastActiveWeapon < len(self.weapons):
                        cmd.weaponSelect = self.lastActiveWeapon
                    self.wasLastWeaponSwitchPressed = True
            else:
                self.wasLastWeaponSwitchPressed = False

            if inputState.isSet("attack2"):
                cmd.buttons |= InputFlag.Attack2
            if inputState.isSet("reload"):
                cmd.buttons |= InputFlag.Reload

        cmd.move = Vec3(0)
        if cmd.buttons & InputFlag.MoveForward:
            cmd.move[1] = BaseSpeed * self.classInfo.ForwardFactor
        elif cmd.buttons & InputFlag.MoveBackward:
            cmd.move[1] = -BaseSpeed * self.classInfo.BackwardFactor
        if cmd.buttons & InputFlag.MoveRight:
            cmd.move[0] = BaseSpeed * self.classInfo.ForwardFactor
        elif cmd.buttons & InputFlag.MoveLeft:
            cmd.move[0] = -BaseSpeed * self.classInfo.ForwardFactor

        #if cmd.move[0] and cmd.move[1]:
        #    cmd.move *= self.DiagonalFactor

        self.considerSendCommand()

        self.mouseDelta = Vec2()

        return task.cont

    def disableControls(self):
        if not self.controlsEnabled:
            return

        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.MAbsolute)

        base.win.requestProperties(props)

        self.accept('escape', self.enableControls)

        self.controlsEnabled = False

    def preDataUpdate(self):
        DistributedTFPlayer.preDataUpdate(self)
        self.wasFreezeFraming = (self.observerMode == ObserverMode.FreezeCam)

    def postDataUpdate(self):
        DistributedTFPlayer.postDataUpdate(self)

        if not self.wasFreezeFraming and self.observerMode == ObserverMode.FreezeCam:
            self.freezeFrameStart = base.camera.getPos()
            self.freezeCamStartTime = globalClock.frame_time
            self.freezeFrameDistance = random.uniform(spec_freeze_distance_min.getValue(), spec_freeze_distance_max.getValue())
            self.freezeZOffset = random.uniform(-30, 20)
            self.sentFreezeFrame = False
        elif self.wasFreezeFraming and self.observerMode != ObserverMode.FreezeCam:
            # Start rendering to the 3D output display region again.  Turns off
            # the freeze frame.
            base.postProcess.freezeFrame.freezeFrame(0.0)
            base.taskMgr.remove('hideSceneFreezeFrame')
            self.__showSceneFreezeFrame()
            #for mgr in base.sfxManagerList:
            #    mgr.setVolume(base.config.GetFloat('sfx-volume', 1))
            if self.killedByLabel:
                self.killedByLabel.destroy()
                self.killedByLabel = None

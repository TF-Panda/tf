""" DistributedTFPlayerOV: Local TF player """

from panda3d.core import WindowProperties, MouseData, Point2, Vec2, Datagram, OmniBoundingVolume, NodePath, Point3, Vec3, lookAt
from panda3d.core import ConfigVariableDouble, InterpolatedVec3, CardMaker

from panda3d.pphysics import PhysSweepResult

from .DistributedTFPlayer import DistributedTFPlayer
from .PlayerCommand import PlayerCommand
from .InputButtons import InputFlag
from .TFClass import *
from .ObserverMode import ObserverMode
from tf.object.ObjectType import ObjectType

from tf.tfgui.TFHud import TFHud
from tf.tfgui.KillFeed import KillFeed
from tf.tfgui.TFWeaponSelection import TFWeaponSelection
from tf.tfbase import TFGlobals

from direct.distributed2.ClientConfig import *
from direct.showbase.InputStateGlobal import inputState
from direct.directbase import DirectRender
from direct.gui.DirectGui import OnscreenText

from tf.tfgui.TFClassMenu import TFClassMenu

import copy
import random

spec_freeze_time = ConfigVariableDouble("spec-freeze-time", 4.0)
spec_freeze_traveltime = ConfigVariableDouble("spec-freeze-travel-time", 0.4)
spec_freeze_distance_min = ConfigVariableDouble("spec-freeze-distance-min", 96)
spec_freeze_distance_max = ConfigVariableDouble("spec-freeze-distance-max", 200)

mouse_sensitivity = ConfigVariableDouble("mouse-sensitivity", 3.0)
mouse_raw_input = ConfigVariableBool("mouse-raw-input", True)

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
CHASE_CAM_DISTANCE = 96.0

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
            self.viewModel.ivLagAngles.clearHistory()

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

        if self.isObserver():
            if self.observerMode == ObserverMode.DeathCam:
                self.calcDeathCamView()
            elif self.observerMode == ObserverMode.FreezeCam:
                self.calcFreezeCamView()
        else:
            base.camera.setPos(self.getEyePosition())
            base.camera.setHpr(self.viewAngles + self.punchAngle)
            if self.viewModel:
                # Also calculate the viewmodel position/rotation.
                self.viewModel.calcView(self, base.camera)

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
        origin = self.getEyePosition()
        if self.isDead():
            if self.ragdoll:
                origin = Point3(self.ragdoll[1].getRagdollPosition())
                origin.z += 40
            elif self.gibs:
                origin = Point3(self.gibs.getHeadPosition())
                origin.z += 40

        if killer and killer != self:
            # Compute angles to look at killer.
            vKiller = killer.getEyePosition() - origin
            qKiller = Quat()
            lookAt(qKiller, vKiller)
            Quat.slerp(qForward, qKiller, interpolation, qForward)

        base.camera.setHpr(qForward.getHpr())

        vForward = qForward.getForward()
        vForward.normalize()
        eyeOrigin = origin + (vForward * -self.observerChaseDistance)

        # Clip against world.
        result = PhysSweepResult()
        toEyeOrigin = eyeOrigin - origin
        toEyeOriginLen = toEyeOrigin.length()
        toEyeOrigin /= toEyeOriginLen
        if base.physicsWorld.boxcast(result, WALL_MINS + origin, WALL_MAXS + origin,
                                     toEyeOrigin, toEyeOriginLen, Vec3(0),
                                     TFGlobals.Contents.Solid, TFGlobals.Contents.Empty,
                                     TFGlobals.CollisionGroup.Empty):
            eyeOrigin = result.getBlock().getPosition()
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

        if target.isDead() and target.ragdoll:
            camDesired = Point3(target.ragdoll[1].getRagdollPosition())
        else:
            camDesired = target.getPos()
        if target.health > 0:
            camDesired[2] += target.viewOffset[2]
        #else:
        #    camDesired[2] += 40
        camTarget = Vec3(camDesired)
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

        # trace so that we're put in front of any walls.
        result = PhysSweepResult()
        camToTarget = targetPos - camTarget
        camToTargetLen = camToTarget.length()
        camToTarget /= camToTargetLen
        if base.physicsWorld.boxcast(result, WALL_MINS + camTarget, WALL_MAXS + camTarget,
                                     camToTarget, camToTargetLen,
                                     Vec3(0), TFGlobals.Contents.Solid, TFGlobals.Contents.Empty,
                                     TFGlobals.CollisionGroup.Empty):
            # The camera's going to be really close to the target.  So we
            # don't end up looking at someone's chest, aim close freezecams
            # at the target's eyes.
            block = result.getBlock()
            targetPos = block.getPosition()
            camTarget = camDesired

            # To stop all close in views looking up at character's chins,
            # move the view up.
            targetPos[2] += abs(camTarget[2] - targetPos[2]) * 0.85
            camToTarget = targetPos - camTarget
            camToTargetLen = camToTarget.length()
            camToTarget /= camToTargetLen
            result2 = PhysSweepResult()
            if base.physicsWorld.boxcast(result2, WALL_MINS + camTarget, WALL_MAXS + camTarget,
                                         camToTarget, camToTargetLen,
                                         Vec3(0), TFGlobals.Contents.Solid, TFGlobals.Contents.Empty,
                                         TFGlobals.CollisionGroup.Empty):
                targetPos = result2.getBlock().getPosition()

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
            base.taskMgr.doMethodLater(0.0, self.__hideSceneFreezeFrame, 'hideSceneFreezeFrame')
            #for mgr in base.sfxManagerList:
            #    mgr.setVolume(0.0)
            if self.killedByLabel:
                self.killedByLabel.destroy()
            if target.isObject():
                text = "You were killed by the "
                if target.health <= 0:
                    text += "late "
                text += "Sentry Gun of "
                builder = target.getBuilder()
                if builder:
                    if builder.health <= 0:
                        text += "the late "
                    text += builder.playerName
            else:
                text = "You were killed by "
                if target.health <= 0:
                    text += "the late "
                text += target.playerName
            text += "!"

            self.killedByLabel = OnscreenText(text = text, scale = 0.09,
                                              pos = (0, 0.9), fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1),
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

    def respawn(self):
        DistributedTFPlayer.respawn(self)
        self.hide()
        self.viewModel.show()
        self.hud.showHud()

    def onTFClassChanged(self):
        DistributedTFPlayer.onTFClassChanged(self)

        if self.tfClass == Class.Engineer and not self.objectPanels:
            self.createObjectPanels()
        elif self.tfClass != Class.Engineer:
            self.destroyObjectPanels()

    def becomeRagdoll(self, forceJoint, forcePosition, forceVector):
        DistributedTFPlayer.becomeRagdoll(self, forceJoint, forcePosition, forceVector)
        self.viewModel.hide()
        self.hud.hideHud()

    def gib(self):
        DistributedTFPlayer.gib(self)
        self.viewModel.hide()
        self.hud.hideHud()

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
        self.disableControls()
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

        self.accept('wheel_up', self.wpnSelect.hoverPrevWeapon)
        self.accept('wheel_down', self.wpnSelect.hoverNextWeapon)
        self.accept(',', self.doChangeClass)

        self.accept('e', self.sendUpdate, ['voiceCommand', [VoiceCommand.Medic]])

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
        if self.classMenu:
            return
        self.classMenu = TFClassMenu()
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
        props.setMouseMode(WindowProperties.MRelative)

        base.win.requestProperties(props)

        #base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)
        if base.mouseWatcherNode.hasMouse():
            md = base.mouseWatcherNode.getMouse()
            sizeX = base.win.getXSize()
            sizeY = base.win.getYSize()
            self.lastMouseSample = Vec2((md.getX() * 0.5 + 0.5) * sizeX, (md.getY() * 0.5 + 0.5) * sizeY)
        else:
            self.lastMouseSample = Vec2()
        self.mouseDelta = Vec2()

        self.accept('escape', self.disableControls)

        self.hud.showHud()

        self.controlsEnabled = True

    def mouseMovement(self, task):
        """
        Runs every frame to get smooth mouse movement.  Delta is accumulated
        over multiple frames for player command tick.
        """

        mw = base.mouseWatcherNode
        if self.controlsEnabled and mw.hasMouse() and not self.isDead():
            md = mw.getMouse()
            sens = mouse_sensitivity.getValue()
            sizeX = base.win.getXSize()
            sizeY = base.win.getYSize()
            #center = Point2(base.win.getXSize() // 2, base.win.getYSize() // 2)
            sample = Vec2((md.getX() * 0.5 + 0.5) * sizeX, (md.getY() * 0.5 + 0.5) * sizeY)
            delta = (sample - self.lastMouseSample) * sens
            #base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

            self.viewAngles[0] -= delta.x * 0.022
            self.viewAngles[1] = max(-90, min(90, self.viewAngles[1] + (delta.y * 0.022)))
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
                if self.wpnSelect.isActive:
                    cmd.weaponSelect = self.wpnSelect.index
                    self.wpnSelect.hide()
                else:
                    cmd.buttons |= InputFlag.Attack1

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

        self.hud.hideHud()

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

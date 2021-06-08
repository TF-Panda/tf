""" DistributedTFPlayerOV: Local TF player """

from panda3d.core import WindowProperties, MouseData, Point2, Vec2, Datagram, OmniBoundingVolume, NodePath, Point3, Vec3, lookAt
from panda3d.core import ConfigVariableDouble

from .DistributedTFPlayer import DistributedTFPlayer
from .PlayerCommand import PlayerCommand
from .InputButtons import InputFlag
from .TFClass import *
from .ObserverMode import ObserverMode

from tf.character.Char import Char
from tf.tfgui.TFHud import TFHud
from tf.tfgui.TFWeaponSelection import TFWeaponSelection
from tf.tfbase import TFGlobals

from direct.distributed2.ClientConfig import *
from direct.showbase.InputStateGlobal import inputState
from direct.directbase import DirectRender
from direct.gui.DirectGui import OnscreenText

import copy
import random

spec_freeze_time = ConfigVariableDouble("spec-freeze-time", 4.0)
spec_freeze_traveltime = ConfigVariableDouble("spec-freeze-travel-time", 0.4)
spec_freeze_distance_min = ConfigVariableDouble("spec-freeze-distance-min", 96)
spec_freeze_distance_max = ConfigVariableDouble("spec-freeze-distance-max", 200)

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
        self.wpnSelect = TFWeaponSelection()
        self.controlsEnabled = False

        # Entities that the player predicts/simulates along with itself.  For
        # instance, weapons.
        self.playerSimulatedEntities = []

        # Add fields predicted by the local player.
        self.addPredictionField("tickBase", int)
        self.addPredictionField("activeWeapon", int, getter=self.getActiveWeapon, setter=self.setActiveWeapon)
        self.addPredictionField("onGround", bool, noErrorCheck=True)

        self.observerChaseDistance = 0
        self.freezeFrameStart = Point3()
        self.freezeCamStartTime = 0.0
        self.freezeFrameDistance = 0.0
        self.freezeZOffset = 0.0
        self.sentFreezeFrame = False
        self.wasFreezeFraming = False

        self.killedByLabel = None

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
            base.camera.setPos(self.getPos() + (0, 0, self.classInfo.ViewHeight))
            base.camera.setHpr(self.viewAngles)

    def calcDeathCamView(self):
        killer = base.net.doId2do.get(self.observerTarget)

        # Swing to face our killer within half the death anim time.
        interpolation = (globalClock.getFrameTime() - self.deathTime) / (TF_DEATH_ANIMATION_TIME * 0.5)
        interpolation = max(0, min(1, interpolation))
        interpolation = TFGlobals.simpleSpline(interpolation)

        self.observerChaseDistance += globalClock.getDt() * 48.0
        self.observerChaseDistance = max(16, min(CHASE_CAM_DISTANCE, self.observerChaseDistance))

        aForward = self.viewAngles
        qForward = Quat()
        qForward.setHpr(aForward)
        origin = self.getPos() + (0, 0, self.classInfo.ViewHeight)
        if self.ragdoll:
            origin = Point3(self.ragdoll[1].getRagdollPosition())
            origin.z += 40

        if killer and killer != self:
            # Compute angles to look at killer.
            vKiller = (killer.getPos() + (0, 0, killer.classInfo.ViewHeight)) - origin
            qKiller = Quat()
            lookAt(qKiller, vKiller)
            Quat.slerp(qForward, qKiller, interpolation, qForward)

        base.camera.setHpr(qForward.getHpr())

        vForward = qForward.getForward()
        vForward.normalize()
        eyeOrigin = origin + (vForward * -self.observerChaseDistance)

        # TODO: Box cast to find walls.

        base.camera.setPos(eyeOrigin)

    def calcFreezeCamView(self):
        curTime = globalClock.getFrameTime() - self.freezeCamStartTime

        target = base.net.doId2do.get(self.observerTarget)
        if not target:
            self.calcDeathCamView()
            return

        # Zoom towards our target.
        blendPerc = max(0, min(1, curTime / spec_freeze_traveltime.getValue()))
        blendPerc = TFGlobals.simpleSpline(blendPerc)

        if target.ragdoll:
            camDesired = Point3(target.ragdoll[1].getRagdollPosition())
        else:
            camDesired = target.getPos()
        if target.health > 0:
            camDesired[2] += target.classInfo.ViewHeight
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
        eyePosZ = target.getZ() + target.classInfo.ViewHeight
        targetPos[2] = eyePosZ + self.freezeZOffset

        # TODO: trace so that we're put in front of any walls.

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
            if self.killedByLabel:
                self.killedByLabel.destroy()
            self.killedByLabel = OnscreenText(text = "You were killed by %s!" % target.playerName, scale = 0.1,
                                              pos = (0, 0.89), fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1),
                                              font = TFGlobals.getTF2SecondaryFont())
            self.sentFreezeFrame = True

    def respawn(self):
        DistributedTFPlayer.respawn(self)
        self.modelNp.hide()
        self.viewModel.show()
        self.hud.showHud()

    def becomeRagdoll(self, forceJoint, forcePosition, forceVector):
        DistributedTFPlayer.becomeRagdoll(self, forceJoint, forcePosition, forceVector)
        self.viewModel.hide()
        self.hud.hideHud()

    def RecvProxy_weapons(self, weapons):
        changed = weapons != self.weapons
        self.weapons = weapons
        if changed:
            self.wpnSelect.rebuildWeaponList()

    def RecvProxy_health(self, hp):
        self.health = hp
        self.hud.updateHealthLabel()

    def RecvProxy_maxHealth(self, maxHp):
        self.maxHealth = maxHp
        self.hud.updateHealthLabel()

    def getNextCommandNumber(self):
        return self.lastOutgoingCommand + self.chokedCommands + 1

    def getNextCommand(self):
        return self.commands[self.getNextCommandNumber() % self.MaxCommands]

    def shouldSendCommand(self):
        return globalClock.getFrameTime() >= self.nextCommandTime and base.cr.connected

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
            delta = max(0.0, min(maxDelta, globalClock.getFrameTime() - self.nextCommandTime))
            self.nextCommandTime = globalClock.getFrameTime() + cmdIval - delta
        else:
            # Not sending yet, but building a list of commands to send.
            self.chokedCommands += 1

    def generate(self):
        DistributedTFPlayer.generate(self)
        base.localAvatar = self
        base.localAvatarId = self.doId

    def delete(self):
        base.simTaskMgr.remove('runControls')
        base.taskMgr.remove('calcView')

        del base.localAvatar
        del base.localAvatarId
        DistributedTFPlayer.delete(self)

    def onModelChanged(self):
        if not self.modelNp:
            return

        self.modelNp.hide()

    def announceGenerate(self):
        DistributedTFPlayer.announceGenerate(self)
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

        self.accept('wheel_up', self.wpnSelect.hoverPrevWeapon)
        self.accept('wheel_down', self.wpnSelect.hoverNextWeapon)

        base.simTaskMgr.add(self.runControls, 'runControls')
        base.taskMgr.add(self.calcViewTask, 'calcView', sort = 38)

        props = WindowProperties()
        props.setTitle(f"Team Fortress - {self.doId}")
        base.win.requestProperties(props)

        self.accept('escape', self.enableControls)

    def calcViewTask(self, task):
        self.calcView()
        return task.cont

    def enableControls(self):
        if self.controlsEnabled:
            return

        base.disableMouse()

        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.MConfined)

        base.win.requestProperties(props)

        base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

        self.accept('escape', self.disableControls)

        self.hud.showHud()

        self.controlsEnabled = True

    def runControls(self, task):
        if self.controlsEnabled and not self.isDead:
            sens = base.config.GetFloat("mouse-sensitivity", 0.1)
            center = Point2(base.win.getXSize() // 2, base.win.getYSize() // 2)
            md = base.win.getPointer(0)
            mouseDx = (md.getX() - center.getX()) * sens
            mouseDy = (md.getY() - center.getY()) * sens
            base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

            base.camera.setH(base.camera.getH() - mouseDx)
            base.camera.setP(max(-90, min(90, base.camera.getP() - mouseDy)))
        else:
            mouseDx = 0
            mouseDy = 0

        cmd = self.getNextCommand()
        cmd.clear()
        cmd.commandNumber = self.getNextCommandNumber()
        rand = random.Random(cmd.commandNumber)
        cmd.randomSeed = rand.randint(0, 0xFFFFFFFF)
        cmd.tickCount = base.tickCount

        cmd.buttons = InputFlag.Empty
        if not self.isDead:
            cmd.viewAngles = base.camera.getHpr()
            cmd.mouseDelta = Vec2(mouseDx, mouseDy)
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
                    #print("Setting weaponSelect to", cmd.weaponSelect)
                    self.wpnSelect.hide()
                else:
                    cmd.buttons |= InputFlag.Attack1
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

        self.considerSendCommand()

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
            self.freezeCamStartTime = globalClock.getFrameTime()
            self.freezeFrameDistance = random.uniform(spec_freeze_distance_min.getValue(), spec_freeze_distance_max.getValue())
            self.freezeZOffset = random.uniform(-30, 20)
            self.sentFreezeFrame = False
        elif self.wasFreezeFraming and self.observerMode != ObserverMode.FreezeCam:
            # Start rendering to the 3D output display region again.  Turns off
            # the freeze frame.
            base.postProcess.freezeFrame.freezeFrame(0.0)
            if self.killedByLabel:
                self.killedByLabel.destroy()
                self.killedByLabel = None

""" DistributedTFPlayerOV: Local TF player """

from panda3d.core import WindowProperties, MouseData, Point2, Vec2, Datagram, OmniBoundingVolume, NodePath, Point3

from .DistributedTFPlayer import DistributedTFPlayer
from .PlayerCommand import PlayerCommand
from .InputButtons import InputFlag

from tf.character.Char import Char
from tf.tfgui.TFHud import TFHud
from tf.tfgui.TFWeaponSelection import TFWeaponSelection

from direct.distributed2.ClientConfig import *
from direct.showbase.InputStateGlobal import inputState

import copy

class DistributedTFPlayerOV(DistributedTFPlayer):

    MaxCommands = 90

    NumNewCmdBits = 4
    MaxNewCommands = ((1 << NumNewCmdBits) - 1)

    NumBackupCmdBits = 3
    MaxBackupCommands = ((1 << NumBackupCmdBits) - 1)

    def __init__(self):
        DistributedTFPlayer.__init__(self)
        self.viewModel = None
        self.commandsSent = 0
        self.lastOutgoingCommand = 0
        self.chokedCommands = 0
        self.nextCommandTime = 0.0
        self.lastCommand = PlayerCommand()
        self.commands = []
        for _ in range(self.MaxCommands):
            self.commands.append(PlayerCommand())
        self.hud = TFHud()
        self.wpnSelect = TFWeaponSelection()
        self.controlsEnabled = False

        self.myRagdoll = None
        self.isDead = False

    def respawn(self):
        DistributedTFPlayer.respawn(self)
        self.isDead = False
        self.removeTask("ragdollControls")
        base.camera.reparentTo(base.render)
        self.ragdollFocusPivot.removeNode()
        self.ragdollFocusPivot = None
        self.myRagdoll = None
        self.modelNp.hide()
        self.viewModel.show()

        base.camera.reparentTo(render)
        base.camera.setPos(self.getPos(render) + (0, 0, self.classInfo.ViewHeight))
        base.camera.setHpr(0, 0, 0)

    def becomeRagdoll(self, forceJoint, forcePosition, forceVector):
        self.isDead = True
        cCopy, rd = DistributedTFPlayer.becomeRagdoll(self, forceJoint, forcePosition, forceVector)
        self.viewModel.hide()
        self.myRagdoll = (cCopy, rd)
        self.ragdollFocusPivot = NodePath("focusPivot")
        self.ragdollFocusPivot.reparentTo(base.render)
        self.ragdollFocusPivot.setHpr(self.getHpr())
        self.ragdollFocusPivot.setP(-10)
        base.camera.reparentTo(self.ragdollFocusPivot)
        base.camera.setPos(0, -200, 0)
        base.camera.setHpr(0, 0, 0)
        self.addTask(self.ragdollControls, "ragdollControls", sim = False, appendTask = True)

    def ragdollControls(self, task):
        if not self.myRagdoll:
            return task.done

        jointPos = self.myRagdoll[1].getJointActor("bip_pelvis").getTransform().getPos()
        pos = Point3(jointPos)
        #pos.y -= 200
        pos.z += 50
        self.ragdollFocusPivot.setPos(pos)

        if self.controlsEnabled:
            sens = base.config.GetFloat("mouse-sensitivity", 0.1)
            center = Point2(base.win.getXSize() // 2, base.win.getYSize() // 2)
            md = base.win.getPointer(0)
            mouseDx = (md.getX() - center.getX()) * sens
            mouseDy = (md.getY() - center.getY()) * sens
            base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

            self.ragdollFocusPivot.setH(self.ragdollFocusPivot.getH() - mouseDx)
            self.ragdollFocusPivot.setP(max(-90, min(90, self.ragdollFocusPivot.getP() - mouseDy)))

        base.camera.setPos(0, -150, 0)
        base.camera.setHpr(0, 0, 0)

        return task.cont

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
        nextCommandNum = self.lastOutgoingCommand + self.chokedCommands + 1

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

        for to in range(nextCommandNum - numCmds + 1, nextCommandNum + 1):
            isNewCmd = to >= (nextCommandNum - newCommands + 1)

            ok = ok and self.writeCommandDelta(dg, prev, to, isNewCmd)
            prev = to

        if ok:
            self.sendUpdate('playerCommand', [dg.getMessage()])
            self.commandsSent += 1

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

        del base.localAvatar
        del base.localAvatarId
        DistributedTFPlayer.delete(self)

    def announceGenerate(self):
        DistributedTFPlayer.announceGenerate(self)
        base.cr.sendTick()
        self.modelNp.hide()

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

        props = WindowProperties()
        props.setTitle(f"Team Fortress - {self.doId}")
        base.win.requestProperties(props)

        self.accept('escape', self.enableControls)

    def setPos(self, pos):
        DistributedTFPlayer.setPos(self, pos)
        base.camera.setPos(self.getPos() + (0, 0, self.classInfo.ViewHeight))

    def enableControls(self):
        if self.controlsEnabled:
            return

        base.disableMouse()

        if not self.isDead:
            base.camera.reparentTo(render)
            base.camera.setPos(self.getPos(render) + (0, 0, self.classInfo.ViewHeight))
            base.camera.setHpr(0, 0, 0)

        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.MConfined)

        base.win.requestProperties(props)

        base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

        self.accept('escape', self.disableControls)

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
                    print("Setting weaponSelect to", cmd.weaponSelect)
                    self.wpnSelect.hide()
                else:
                    cmd.buttons |= InputFlag.Attack1
            if inputState.isSet("attack2"):
                cmd.buttons |= InputFlag.Attack2
            if inputState.isSet("reload"):
                cmd.buttons |= InputFlag.Reload

        #self.runPlayerCommand(cmd, globalClock.getDt())
        #base.camera.setPos(self.np.getPos() + (0, 0, self.classInfo.ViewHeight))

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

        self.controlsEnabled = False

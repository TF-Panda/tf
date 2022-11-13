"""VoiceCommandMenu module: contains the VoiceCommandMenu class."""

from panda3d.core import Point3, TextNode

from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject

from tf.tfbase import TFGlobals

class VoiceCommandMenu(DirectObject):

    def __init__(self):
        self.frame = DirectFrame(parent=base.a2dLeftCenter)
        self.frame.setPos(0.1, 0, 0)
        self.frame['frameColor'] = (0.1, 0.1, 0.1, 0.7)
        self.frame['relief'] = DGG.FLAT
        self.frame.setBin('gui-popup', 100)
        self.items = []
        self.currFade = 0.0
        self.targetFade = 0.0
        self.fadingOut = False
        self.updateTask = None
        self.frameStale = True
        self.active = False
        self.frame.hide()
        self.lblRoot = self.frame.attachNewNode("lblRoot")

    def cleanup(self):
        self.stopUpdateTask()
        for lbl, _, _ in self.items:
            lbl.destroy()
        self.items = None
        self.ignoreAll()
        self.lblRoot.removeNode()
        self.lblRoot = None
        self.frame.destroy()
        self.frame = None
        self.active = None

    def addItem(self, text, hotkey, cmd):
        lbl = OnscreenText(str(hotkey) + ". " + text, parent=self.lblRoot,
                           fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1), font=TFGlobals.getTF2SecondaryFont(),
                           align=TextNode.ALeft, scale=0.045)
        self.items.append((lbl, hotkey, cmd))
        self.frameStale = True

    def startUpdateTask(self):
        self.stopUpdateTask()

        self.updateTask = base.taskMgr.add(self.__update, 'voiceCmdMenuUpdate')

    def stopUpdateTask(self):
        if self.updateTask:
            self.updateTask.remove()
            self.updateTask = None

    def updateFrame(self):
        lblSpacing = 0.05
        z = lblSpacing * (len(self.items) / 2)
        for lbl, _, _ in self.items:
            lbl.setPos(0, z)
            z -= lblSpacing
        mins = Point3()
        maxs = Point3()
        self.lblRoot.calcTightBounds(mins, maxs)
        hPad = 0.03
        vPad = 0.03
        self.frame['frameSize'] = (mins[0] - hPad, maxs[0] + hPad, mins[2] - vPad, maxs[2] + vPad)

    def show(self):
        if self.frameStale:
            self.updateFrame()
            self.frameStale = False
        self.fadingOut = False
        self.targetFade = 1.0
        self.frame.show()
        for _, hotkey, cmd in self.items:
            self.accept(str(hotkey), self.__handleCommand, [cmd])
        self.startUpdateTask()
        self.active = True

    def hide(self, fadeOut=True):
        if fadeOut:
            self.targetFade = 0.0
            self.fadingOut = True
        else:
            self.frame.hide()
            self.currFade = 0.0
            self.stopUpdateTask()
        self.ignoreAll()
        self.active = False

    def __handleCommand(self, cmd):
        if not self.active:
            return

        assert base.localAvatar.voiceCommandMenus[base.localAvatar.currentVoiceCommandMenu] == self
        base.localAvatar.sendUpdate('voiceCommand', [cmd])
        base.localAvatar.disableCurrentVoiceCommandMenu()

    def __update(self, task):
        if self.currFade != self.targetFade:
            self.currFade = TFGlobals.approach(self.targetFade, self.currFade, globalClock.dt / 0.3)
            self.frame.setAlphaScale(self.currFade)
            if self.fadingOut and self.currFade <= 0:
                self.frame.hide()
                self.stopUpdateTask()
                return task.done

        return task.cont

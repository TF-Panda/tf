"""VoiceCommandMenu module: contains the VoiceCommandMenu class."""

from panda3d.core import Point3, TextNode

from direct.gui.DirectGui import *
from tf.tfbase import TFGlobals

from . import TFGuiProperties
from .GuiPanel import GuiPanel


class VoiceCommandMenu(GuiPanel):

    def __init__(self):
        GuiPanel.__init__(self, parent=base.a2dLeftCenter)
        self.setPos(0.1, 0, 0)
        self['frameColor'] = TFGuiProperties.BackgroundColorNeutralTranslucent
        self['relief'] = DGG.FLAT
        self.items = []
        self.currFade = 0.0
        self.targetFade = 0.0
        self.fadingOut = False
        self.updateTask = None
        self.frameStale = True
        self.active = False
        GuiPanel.hide(self)
        self.lblRoot = self.attachNewNode("lblRoot")

        self.initialiseoptions(VoiceCommandMenu)

    def cleanup(self):
        self.stopUpdateTask()
        for lbl, _, _ in self.items:
            lbl.destroy()
        self.items = None
        self.ignoreAll()
        self.lblRoot.removeNode()
        self.lblRoot = None
        self.active = None
        self.destroy()

    def addItem(self, text, hotkey, cmd):
        lbl = OnscreenText(str(hotkey) + ". " + text, parent=self.lblRoot,
                           fg=TFGuiProperties.TextColorLight, shadow=TFGuiProperties.TextShadowColor, font=TFGlobals.getTF2SecondaryFont(),
                           align=TextNode.ALeft, scale=0.045)
        self.items.append((lbl, hotkey, cmd))
        self.bindButton(str(hotkey), self.__handleCommand, [cmd])
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
        self['frameSize'] = (mins[0] - hPad, maxs[0] + hPad, mins[2] - vPad, maxs[2] + vPad)

    def show(self):
        if self.frameStale:
            self.updateFrame()
            self.frameStale = False
        self.fadingOut = False
        self.targetFade = 1.0
        GuiPanel.show(self)
        self.openPanel()
        self.startUpdateTask()
        self.active = True

    def hide(self, fadeOut=True):
        if fadeOut:
            self.targetFade = 0.0
            self.fadingOut = True
        else:
            GuiPanel.hide(self)
            self.currFade = 0.0
            self.stopUpdateTask()
        self.closePanel()
        self.active = False

    def __handleCommand(self, cmd):
        if not self.active:
            return

        assert base.localAvatar.voiceCommandMenus[base.localAvatar.currentVoiceCommandMenu] == self
        base.localAvatar.sendUpdate('voiceCommand', [cmd])
        base.localAvatar.disableCurrentVoiceCommandMenu()

    def __update(self, task):
        if self.currFade != self.targetFade:
            self.currFade = TFGlobals.approach(self.targetFade, self.currFade, base.clockMgr.getDeltaTime() / 0.3)
            self.setAlphaScale(self.currFade)
            if self.fadingOut and self.currFade <= 0:
                GuiPanel.hide(self)
                self.stopUpdateTask()
                return task.done

        return task.cont

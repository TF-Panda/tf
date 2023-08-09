
from panda3d.core import NodePath, TextNode

from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.gui.DirectGui import DGG, DirectFrame, DirectWaitBar, OnscreenText
from tf.tfbase import TFGlobals, TFLocalizer
from tf.tfgui import TFGuiProperties


class ObjectPanel(NodePath):

    def __init__(self):
        NodePath.__init__(self, 'objectpanel')

        self.frame = DirectFrame(relief = DGG.FLAT,
                                 state = DGG.NORMAL,
                                 frameColor = (1, 0.5, 0.5, 0.8),
                                 frameSize = (-2, 2, -1, 1),
                                 parent = self,
                                 suppressMouse = False)

        # Unplaced/placed
        self.topFSM = ClassicFSM('ObjectPanelTop',
          [
            State('off', self.enterOff, self.exitOff),
            State('unbuilt', self.enterNotBuilt, self.exitNotBuilt),
            State('built', self.enterBuilt, self.exitBuilt)
          ], 'off', 'off')
        # Built states
        self.builtFSM = ClassicFSM('ObjectPanelBuilt',
          [
            State('off', self.enterBuiltOff, self.exitBuiltOff),
            State('building', self.enterBuiltBuilding, self.exitBuiltBuilding),
            State('active', self.enterBuiltActive, self.exitBuiltActive)
          ], 'off', 'off')

        self.topFSM.enterInitialState()
        self.builtFSM.enterInitialState()

        self.object = None

        self.objectName = TFLocalizer.Object
        self.setScale(0.125)
        self.setX(0.28)
        self.setZ(-0.1)

        self.titleLbl = OnscreenText(text = self.objectName, font = TFGlobals.getTF2SecondaryFont(),
            parent = self.frame, scale = 0.325, fg=TFGuiProperties.TextColorLight,
            shadow=TFGuiProperties.TextShadowColor, pos = (0, 0.7))

    def destroy(self):
        self.builtFSM.requestFinalState()
        self.topFSM.requestFinalState()
        self.titleLbl.destroy()
        del self.titleLbl
        self.frame.destroy()
        del self.frame
        self.object = None
        self.topFSM = None
        self.builtFSM = None
        self.removeNode()

    def setObject(self, obj):
        # Sets the object associated with the panel.
        self.object = obj
        self.updateState()

    def updateState(self):
        if not self.object:
            self.builtFSM.request('off')
            self.topFSM.request('unbuilt')
            return

        if self.object.isBuilding():
            self.topFSM.request('built')
            self.builtFSM.request('building')
            self.updateBuildingBar()

        elif self.object.isActive():
            self.topFSM.request('built')
            self.builtFSM.request('active')
            self.levelLbl.setText(str(self.object.level))

        self.updateHealthBar()

    def updateHealthBar(self):
        if not self.object:
            return

        hpFrac = self.object.health / self.object.maxHealth
        self.hpBar['value'] = hpFrac

    def updateBuildingBar(self):
        self.buildingBar['value'] = self.object.getCycle()

    def enterOff(self):
        self.reparentTo(hidden)

    def exitOff(self):
        self.reparentTo(base.a2dTopLeft)

    def enterNotBuilt(self):
        self.frame['frameColor'] = TFGuiProperties.BackgroundColorNeutralTranslucent
        self.nbLabel = OnscreenText(
            text = TFLocalizer.NotBuilt,
            fg = TFGuiProperties.TextColorLight, shadow=TFGuiProperties.TextShadowColor,
            pos = (0, -0.1),
            scale = 0.35,
            font = TFGlobals.getTF2SecondaryFont(),
            parent = self.frame)

    def exitNotBuilt(self):
        self.nbLabel.destroy()
        del self.nbLabel

    def enterBuilt(self):
        if self.object.team == TFGlobals.TFTeam.Red:
            self.frame['frameColor'] = TFGuiProperties.BackgroundColorRedTranslucent
        else:
            self.frame['frameColor'] = TFGuiProperties.BackgroundColorBlueTranslucent
        self.hpBar = DirectWaitBar(
            parent = self.frame,
            relief = DGG.FLAT,
            frameColor=TFGuiProperties.BackgroundColorNeutralOpaque,
            barColor=TFGuiProperties.TextColorLight,
            range=1.0,
            value=0.7,
            suppressMouse=False
        )
        self.hpBar.setR(-90)
        self.hpBar.setScale(0.8, 1, 1.2)
        self.hpBar.setX(-1.7)
        self.hpBar.setZ(0)

        self.updateHealthBar()

    def exitBuilt(self):
        self.hpBar.destroy()
        del self.hpBar

    def enterBuiltOff(self):
        pass

    def exitBuiltOff(self):
        pass

    def enterBuiltBuilding(self):
        self.buildingLbl = OnscreenText(
            text = TFLocalizer.Building, scale = 0.35,
            fg = TFGuiProperties.TextColorLight, shadow = TFGuiProperties.TextShadowColor,
            pos = (0, 0), parent = self.frame,
            font = TFGlobals.getTF2SecondaryFont())
        self.buildingBar = DirectWaitBar(
            parent = self,
            frameColor=TFGuiProperties.BackgroundColorNeutralOpaque,
            barColor=TFGuiProperties.TextColorLight,
            range = 1.0,
            value = 0.4,
            relief = DGG.FLAT,
            suppressMouse = False
        )
        self.buildingBar.setZ(-0.3)
        self.buildingBar.setSx(1.18)

    def exitBuiltBuilding(self):
        self.buildingLbl.destroy()
        del self.buildingLbl
        self.buildingBar.destroy()
        del self.buildingBar

    def enterBuiltActive(self):
        self.levelLbl = OnscreenText(
            text = "2",
            scale = 0.3,
            font = TFGlobals.getTF2SecondaryFont(),
            fg = TFGuiProperties.TextColorLight,
            shadow = TFGuiProperties.TextShadowColor,
            parent = self.frame,
            pos = (1.8, 0.7)
        )

    def exitBuiltActive(self):
        self.levelLbl.destroy()
        del self.levelLbl

class SentryPanel(ObjectPanel):

    def __init__(self):
        ObjectPanel.__init__(self)
        self.objectName = TFLocalizer.SentryGun
        self.frame['frameSize'] = (-2, 2, -1.25, 1)
        self.titleLbl.setText(self.objectName)
        self.setZ(-0.15)

    def enterBuilt(self):
        ObjectPanel.enterBuilt(self)
        self.hpBar.setZ(-0.125)
        self.hpBar.setSx(0.95)

    def updateState(self):
        if not self.object:
            ObjectPanel.updateState(self)
            return

        ObjectPanel.updateState(self)
        if self.object.isActive():
            self.updateShellsBar()

    def updateShellsBar(self):
        if not self.object:
            return

        self.killsLbl.setText(TFLocalizer.SentryKillsText % (self.object.numKills, self.object.numAssists))

        shellsFrac = self.object.ammoShells / self.object.maxAmmoShells
        self.shellsBar['value'] = shellsFrac
        if self.object.level < 3:
            upgradeFrac = self.object.upgradeMetal / 200
            self.upgradeBar['value'] = upgradeFrac
        else:
            self.upgradeLbl.setText("Rockets")
            rocketsFrac = self.object.ammoRockets / self.object.maxAmmoRockets
            self.upgradeBar['value'] = rocketsFrac

    def enterBuiltActive(self):
        ObjectPanel.enterBuiltActive(self)

        self.killsLbl = OnscreenText(
            text = TFLocalizer.SentryKillsText % (0, 0),
            scale = 0.3,
            fg = TFGuiProperties.TextColorLight,
            shadow = TFGuiProperties.TextShadowColor,
            parent = self.frame,
            pos = (-1.2, 0.25),
            align = TextNode.ALeft,
            font = TFGlobals.getTF2SecondaryFont()
        )

        self.shellsLbl = OnscreenText(
            text = TFLocalizer.Shells,
            scale = 0.28,
            fg = TFGuiProperties.TextColorLight,
            shadow = TFGuiProperties.TextShadowColor,
            parent = self.frame,
            pos = (-1.2, -0.1),
            align = TextNode.ALeft,
            font = TFGlobals.getTF2SecondaryFont()
        )
        self.shellsBar = DirectWaitBar(
            parent = self.frame,
            frameColor = TFGuiProperties.BackgroundColorNeutralOpaque,
            barColor = TFGuiProperties.TextColorLight,
            range = 1.0,
            value = 0.4,
            relief = DGG.FLAT,
            suppressMouse = False
        )
        self.shellsBar.setZ(-0.25)
        self.shellsBar.setSx(1.18)

        self.upgradeLbl = OnscreenText(
            text = TFLocalizer.Upgrade,
            scale = 0.28,
            fg = TFGuiProperties.TextColorLight,
            shadow = TFGuiProperties.TextShadowColor,
            parent = self.frame,
            pos = (-1.2, -0.6),
            align = TextNode.ALeft,
            font = TFGlobals.getTF2SecondaryFont()
        )
        self.upgradeBar = DirectWaitBar(
            parent = self.frame,
            frameColor = TFGuiProperties.BackgroundColorNeutralOpaque,
            barColor = TFGuiProperties.TextColorLight,
            range = 1.0,
            value = 0.4,
            relief = DGG.FLAT,
            suppressMouse = False
        )
        self.upgradeBar.setZ(-0.8)
        self.upgradeBar.setSx(1.18)

        self.updateShellsBar()

    def exitBuiltActive(self):
        ObjectPanel.exitBuiltActive(self)

        self.killsLbl.destroy()
        del self.killsLbl
        self.shellsLbl.destroy()
        del self.shellsLbl
        self.shellsBar.destroy()
        del self.shellsBar
        self.upgradeLbl.destroy()
        del self.upgradeLbl
        self.upgradeBar.destroy()
        del self.upgradeBar

class DispenserPanel(ObjectPanel):

    def __init__(self):
        ObjectPanel.__init__(self)
        self.objectName = TFLocalizer.Dispenser
        self.titleLbl.setText(self.objectName)
        self.setZ(-0.445)

class EntrancePanel(ObjectPanel):

    def __init__(self):
        ObjectPanel.__init__(self)
        self.objectName = TFLocalizer.Entrance
        self.titleLbl.setText(self.objectName)
        self.setZ(-0.715)

class ExitPanel(ObjectPanel):

    def __init__(self):
        ObjectPanel.__init__(self)
        self.objectName = TFLocalizer.Exit
        self.titleLbl.setText(self.objectName)
        self.setZ(-0.985)

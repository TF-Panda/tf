"""DistributedPDA module: contains the DistributedPDA class."""

from panda3d.core import *

from direct.fsm.FSM import FSM
from direct.gui.DirectGui import *
from tf.object.ObjectDefs import ObjectDefs
from tf.object.ObjectType import ObjectType
from tf.tfbase import TFGlobals, TFLocalizer
from tf.tfgui import TFGuiProperties
from tf.tfgui.GuiPanel import GuiPanel

from .TFWeapon import TFWeapon
from .WeaponMode import TFWeaponType


class ConstructionObject(NodePath, FSM):

    def __init__(self, parent, objName, metal, hotkey):
        NodePath.__init__(self, 'obj')
        FSM.__init__(self, 'ConstructionObject')

        self.hotkey = hotkey
        self.metal = metal

        self.reparentTo(parent)

        self.frame = DirectFrame(relief = DGG.FLAT,
                                 state = DGG.NORMAL,
                                 frameColor = TFGuiProperties.BackgroundColorNeutralTranslucent,
                                 frameSize = (-0.25, 0.25, -0.25, 0.25),
                                 parent = self,
                                 suppressMouse = False)

        self.nameLbl = OnscreenText(text=objName, align=TextNode.ACenter, parent=self, pos=(0, 0.1), fg=(1, 1, 1, 1), font=TFGlobals.getTF2SecondaryFont())
        self.metalLbl = OnscreenText(text=TFLocalizer.RequiredMetal % metal, align=TextNode.ACenter, parent=self, pos=(0, 0), fg=(1, 1, 1, 1), font=TFGlobals.getTF2SecondaryFont())
        self.hotkeyLbl = OnscreenText(text=TFLocalizer.PressKey % hotkey, align=TextNode.ACenter, parent=self, pos=(0, -0.1), fg=(1, 1, 1, 1), font=TFGlobals.getTF2SecondaryFont())

    def frameColor(self, color):
        self.frame['frameColor'] = color

    def textColor(self, color):
        self.nameLbl['fg'] = color
        self.metalLbl['fg'] = color
        self.hotkeyLbl['fg'] = color

    def enterAlreadyBuilt(self):
        self.frameColor(TFGuiProperties.BackgroundColorNeutralTranslucent)
        self.textColor(TFGuiProperties.TextColorLight)
        self.metalLbl.setText(TFLocalizer.ObjectAlreadyBuilt)
        self.metalLbl.show()
        self.hotkeyLbl.hide()

    def enterAvailable(self):
        self.frameColor(TFGuiProperties.TextColorLight)
        self.textColor(TFGuiProperties.TextColorDark)
        self.metalLbl.show()
        self.metalLbl.setText(TFLocalizer.RequiredMetal % self.metal)
        self.hotkeyLbl.show()
        self.hotkeyLbl.setText(TFLocalizer.PressKey % self.hotkey)

    def enterNotEnoughMetal(self):
        self.frameColor(TFGuiProperties.BackgroundColorNeutralTranslucent)
        self.textColor(TFGuiProperties.TextColorLight)
        self.metalLbl.show()
        self.metalLbl.setText(TFLocalizer.RequiredMetal % self.metal)
        self.hotkeyLbl.show()
        self.hotkeyLbl['fg'] = (0.75, 0, 0, 1)
        self.hotkeyLbl.setText(TFLocalizer.NotEnoughMetal)

    def destroy(self):
        self.nameLbl.destroy()
        self.nameLbl = None
        self.metalLbl.destroy()
        self.metalLbl = None
        self.hotkeyLbl.destroy()
        self.hotkeyLbl = None
        self.frame.destroy()
        self.frame = None
        self.removeNode()

class ConstructionScreen(GuiPanel):

    def __init__(self, player, wpn):
        self.player = player
        GuiPanel.__init__(self, relief=DGG.FLAT, state=DGG.NORMAL,
                          frameColor=TFGuiProperties.BackgroundColorNeutralTranslucent,
                          frameSize=(-1.25, 1.25, -0.5, 0.5),
                          parent=base.aspect2d,
                          suppressMouse = False)

        self.lbl = OnscreenText(text=TFLocalizer.BUILD, parent=self, pos=(-1.16, 0.34), fg=TFGuiProperties.TextColorLight,
            scale=0.15, align=TextNode.ALeft, font=TFGlobals.getTF2BuildFont(), shadow=TFGuiProperties.TextShadowColor)

        self.buildings = []

        x = -0.9
        spacing = 0.6

        key = 1
        for objType, objDef in list(ObjectDefs.items()):
            o = ConstructionObject(self, TFLocalizer.getLocalizedString(objDef['name']),
                                   objDef['cost'], str(key))
            o.setX(x)
            self.bindButton(str(key), wpn.sendUpdate, ['selectBuilding', [objType]])
            self.buildings.append(o)
            x += spacing
            key += 1

        self.updateBuildingStates()

        self.accept('localPlayerMetalChanged', self.updateBuildingStates)
        self.accept('localPlayerObjectsChanged', self.updateBuildingStates)

        self.openPanel()

        self.initialiseoptions(ConstructionScreen)

    def updateBuildingStates(self):
        for i in range(len(self.buildings)):
            b = self.buildings[i]
            if self.player.hasObject(i):
                b.request('AlreadyBuilt')
            elif self.player.metal < b.metal:
                b.request('NotEnoughMetal')
            else:
                b.request('Available')

    def destroy(self):
        self.ignoreAll()
        self.player = None
        self.lbl.destroy()
        self.lbl = None
        for b in self.buildings:
            b.destroy()
        self.buildings = None
        GuiPanel.destroy(self)

class DistributedConstructionPDA(TFWeapon):

    WeaponModel = "models/weapons/w_builder"
    WeaponViewModel = "models/weapons/v_builder_engineer"
    UsesViewModel = True
    MinViewModelOffset = (10, 0, -8)

    def __init__(self):
        TFWeapon.__init__(self)
        self.weaponType = TFWeaponType.PDA
        self.usesClip = False
        self.usesAmmo = False
        self.screen = None

    def activate(self):
        if not TFWeapon.activate(self):
            return False

        if IS_CLIENT and self.isOwnedByLocalPlayer():
            self.createScreen()

    def deactivate(self):
        TFWeapon.deactivate(self)
        if IS_CLIENT and self.isOwnedByLocalPlayer():
            self.destroyScreen()

    def createScreen(self):
        """
        Creates the construction UI.
        """
        self.destroyScreen()
        self.screen = ConstructionScreen(self.player, self)

    def destroyScreen(self):
        if self.screen:
            self.screen.destroy()
            self.screen = None

    def primaryAttack(self):
        pass

    def secondaryAttack(self):
        pass

    def getName(self):
        return TFLocalizer.ConstructionPDA

    if not IS_CLIENT:
        def selectBuilding(self, index):
            if base.air.clientSender != self.player.owner:
                return

            index = max(0, min(ObjectType.COUNT - 1, index))
            if not self.active or self.player.hasObject(index):
                return

            if self.player.metal < ObjectDefs[index]['cost']:
                return

            self.player.selectedBuilding = index
            # Go to toolbox.
            self.player.setActiveWeapon(len(self.player.weapons) - 1)

class DistributedDestructionPDA(TFWeapon):

    WeaponModel = "models/weapons/w_pda_engineer"
    WeaponViewModel = "models/weapons/v_pda_engineer"
    UsesViewModel = True
    MinViewModelOffset = (10, 0, -8)

    def __init__(self):
        TFWeapon.__init__(self)
        self.weaponType = TFWeaponType.PDA
        self.usesClip = False
        self.usesAmmo = False

    def activate(self):
        if not TFWeapon.activate(self):
            return False

        if IS_CLIENT and self.isOwnedByLocalPlayer():
            key = 1
            for objType in list(ObjectDefs.keys()):
                self.accept(str(key), self.sendUpdate, ['destroyBuilding', [objType]])
                key += 1

    def deactivate(self):
        TFWeapon.deactivate(self)
        if IS_CLIENT and self.isOwnedByLocalPlayer():
            key = 1
            for _ in list(ObjectDefs.items()):
                self.ignore(str(key))
                key += 1

    def primaryAttack(self):
        pass

    def secondaryAttack(self):
        pass

    if not IS_CLIENT:
        def destroyBuilding(self, index):
            index = max(0, min(ObjectType.COUNT - 1, index))
            if not self.player or not self.active:
                return

            # Ensure another client didn't try to send this.
            if base.air.clientSender != self.player.owner:
                return

            self.player.destroyObject(index)

    def getName(self):
        return TFLocalizer.DestructionPDA

if not IS_CLIENT:
    DistributedConstructionPDAAI = DistributedConstructionPDA
    DistributedConstructionPDAAI.__name__ = 'DistributedConstructionPDAAI'
    DistributedDestructionPDAAI = DistributedDestructionPDA
    DistributedDestructionPDAAI.__name__ = 'DistributedDestructionPDAAI'

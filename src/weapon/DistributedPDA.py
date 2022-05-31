"""DistributedPDA module: contains the DistributedPDA class."""

from .TFWeapon import TFWeapon

from .WeaponMode import TFWeaponType, TFWeaponMode

from tf.tfbase import TFLocalizer, TFGlobals
from direct.gui.DirectGui import *
from tf.actor.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent

from direct.fsm.FSM import FSM
from direct.showbase.DirectObject import DirectObject

from panda3d.core import *

class ConstructionObject(NodePath, FSM):

    def __init__(self, parent, objName, metal, hotkey):
        NodePath.__init__(self, 'obj')
        FSM.__init__(self, 'ConstructionObject')

        self.hotkey = hotkey
        self.metal = metal

        self.reparentTo(parent)

        self.frame = DirectFrame(relief = DGG.FLAT,
                                 state = DGG.NORMAL,
                                 frameColor = (0, 0.0, 0.0, 0.5),
                                 frameSize = (-0.25, 0.25, -0.25, 0.25),
                                 parent = self,
                                 suppressMouse = False)

        self.nameLbl = OnscreenText(text=objName, align=TextNode.ACenter, parent=self, pos=(0, 0.1), fg=(1, 1, 1, 1), font=TFGlobals.getTF2SecondaryFont())
        self.metalLbl = OnscreenText(text="%i Metal" % metal, align=TextNode.ACenter, parent=self, pos=(0, 0), fg=(1, 1, 1, 1), font=TFGlobals.getTF2SecondaryFont())
        self.hotkeyLbl = OnscreenText(text="Press %s" % hotkey, align=TextNode.ACenter, parent=self, pos=(0, -0.1), fg=(1, 1, 1, 1), font=TFGlobals.getTF2SecondaryFont())

    def frameColor(self, color):
        self.frame['frameColor'] = color

    def textColor(self, color):
        self.nameLbl['fg'] = color
        self.metalLbl['fg'] = color
        self.hotkeyLbl['fg'] = color

    def enterAlreadyBuilt(self):
        self.frameColor((0.0, 0.0, 0.0, 0.5))
        self.textColor((0.5, 0.5, 0.5, 1.0))
        self.metalLbl.setText("Already Built")
        self.metalLbl.show()
        self.hotkeyLbl.hide()

    def enterAvailable(self):
        self.frameColor((0.9, 0.9, 0.9, 0.75))
        self.textColor((0.2, 0.2, 0.2, 1.0))
        self.metalLbl.show()
        self.metalLbl.setText("%i Metal" % self.metal)
        self.hotkeyLbl.show()
        self.hotkeyLbl.setText("Press %s" % self.hotkey)

    def enterNotEnoughMetal(self):
        self.frameColor((0.0, 0.0, 0.0, 0.5))
        self.textColor((0.5, 0.5, 0.5, 1.0))
        self.metalLbl.show()
        self.metalLbl.setText("%i Metal" % self.metal)
        self.hotkeyLbl.show()
        self.hotkeyLbl['fg'] = (0.75, 0, 0, 1)
        self.hotkeyLbl.setText("Not Enough Metal")

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

class ConstructionScreen(DirectObject):

    def __init__(self, player):
        self.player = player
        self.f = DirectFrame(relief=DGG.FLAT, state=DGG.NORMAL,
                        frameColor=(0, 0, 0, 0.5),
                        frameSize=(-1.25, 1.25, -0.5, 0.5),
                        parent=base.aspect2d,
                        suppressMouse = False)

        self.lbl = OnscreenText(text="BUILD", parent=self.f, pos=(-1.16, 0.34), fg=(1, 1, 1, 1), scale=0.15, align=TextNode.ALeft, font=TFGlobals.getTF2BuildFont(), shadow=(0, 0, 0, 0.7))

        x = -0.9
        spacing = 0.6

        s = ConstructionObject(self.f, "Sentry Gun", 130, "1")
        s.setX(x)

        x += spacing

        d = ConstructionObject(self.f, "Dispenser", 100, "2")
        d.setX(x)

        x += spacing

        en = ConstructionObject(self.f, "Entrance", 50, "3")
        en.setX(x)

        x += spacing

        ex = ConstructionObject(self.f, "Exit", 50, "4")
        ex.setX(x)

        self.buildings = [s, d, en, ex]

        self.updateBuildingStates()

        self.accept('localPlayerMetalChanged', self.updateBuildingStates)
        self.accept('localPlayerObjectsChanged', self.updateBuildingStates)

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
        self.f.destroy()
        self.f = None

class DistributedConstructionPDA(TFWeapon):

    WeaponModel = "models/weapons/w_builder"
    WeaponViewModel = "models/weapons/v_builder_engineer"
    UsesViewModel = True

    Metal = [130, 100, 50, 50]

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
            self.accept('1', self.sendUpdate, ['selectBuilding', [0]])
            self.accept('2', self.sendUpdate, ['selectBuilding', [1]])
            self.accept('3', self.sendUpdate, ['selectBuilding', [2]])
            self.accept('4', self.sendUpdate, ['selectBuilding', [3]])

    def deactivate(self):
        TFWeapon.deactivate(self)
        if IS_CLIENT and self.isOwnedByLocalPlayer():
            self.destroyScreen()
            self.ignore('1')
            self.ignore('2')
            self.ignore('3')
            self.ignore('4')

    def createScreen(self):
        """
        Creates the construction UI.
        """
        self.destroyScreen()
        self.screen = ConstructionScreen(self.player)

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

            index = max(0, min(3, index))
            if not self.active or self.player.hasObject(index):
                return

            if self.player.metal < self.Metal[index]:
                return

            self.player.selectedBuilding = index
            # Go to toolbox.
            self.player.setActiveWeapon(len(self.player.weapons) - 1)

class DistributedDestructionPDA(TFWeapon):

    WeaponModel = "models/weapons/w_pda_engineer"
    WeaponViewModel = "models/weapons/v_pda_engineer"
    UsesViewModel = True

    def __init__(self):
        TFWeapon.__init__(self)
        self.weaponType = TFWeaponType.PDA
        self.usesClip = False
        self.usesAmmo = False

    def activate(self):
        if not TFWeapon.activate(self):
            return False

        if IS_CLIENT and self.isOwnedByLocalPlayer():
            self.accept('1', self.sendUpdate, ['destroyBuilding', [0]])
            self.accept('2', self.sendUpdate, ['destroyBuilding', [1]])
            self.accept('3', self.sendUpdate, ['destroyBuilding', [2]])
            self.accept('4', self.sendUpdate, ['destroyBuilding', [3]])

    def deactivate(self):
        TFWeapon.deactivate(self)
        if IS_CLIENT and self.isOwnedByLocalPlayer():
            self.ignore('1')
            self.ignore('2')
            self.ignore('3')
            self.ignore('4')

    def primaryAttack(self):
        pass

    def secondaryAttack(self):
        pass

    if not IS_CLIENT:
        def destroyBuilding(self, index):
            index = max(0, min(3, index))
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

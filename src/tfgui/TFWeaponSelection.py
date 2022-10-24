from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject

from panda3d.core import TextNode

class TFWeaponSelection(DirectObject):

    HoverScale = 0.1
    IdleScale = 0.08
    IdleColor = (0.75, 0.75, 0.75, 1)
    HoverColor = (1, 1, 1, 1)
    InactiveTime = 3.0

    WeaponSpacing = 0.1

    def __init__(self):
        self.root = base.a2dRightCenter.attachNewNode("WeaponSelectionRoot")
        self.root.hide()
        self.scrollSound = base.loader.loadSfx("audio/sfx/wpn_moveselect.ogg")
        self.root.setX(-0.1)
        self.wpnList = []
        self.index = 0
        self.isActive = False
        self.activeTime = 0.0

    def destroy(self):
        self.scrollSound = None
        self.wpnList = None
        self.root.removeNode()
        self.root = None

    def clearWeaponList(self):
        for _, item in self.wpnList:
            item.destroy()
        self.wpnList = []

    def rebuildWeaponList(self):
        self.clearWeaponList()

        topZ = self.WeaponSpacing * ((len(base.localAvatar.getWeapons()) - 1) / 2)

        for i in range(len(base.localAvatar.getWeapons())):
            wpnId = base.localAvatar.weapons[i]
            wpn = base.cr.doId2do.get(wpnId)
            if not wpn:
                return

            z = topZ - (i * self.WeaponSpacing)

            label = OnscreenText(parent = self.root, align = TextNode.ARight,
                                 scale = self.IdleScale, fg = self.IdleColor, shadow = (0, 0, 0, 1),
                                 text = wpn.getName(), pos = (0, z))
            self.wpnList.append((wpnId, label))

    def hoverWeapon(self, index):
        if index < 0 or index >= len(self.wpnList):
            self.hide()
            return

        for i in range(len(self.wpnList)):
            label = self.wpnList[i][1]
            if i == index:
                # Hovering over this one.
                label['fg'] = self.HoverColor
                label.setScale(self.HoverScale)
            else:
                label['fg'] = self.IdleColor
                label.setScale(self.IdleScale)
        self.index = index
        self.scrollSound.play()
        self.activeTime = globalClock.frame_time

    def hoverNextWeapon(self):
        if base.localAvatar.isDead() or base.localAvatar.isLoser():
            return

        if not self.isActive:
            self.show()

        self.hoverWeapon((self.index + 1) % len(base.localAvatar.getWeapons()))

    def hoverPrevWeapon(self):
        if base.localAvatar.isDead() or base.localAvatar.isLoser():
            return

        if not self.isActive:
            self.show()

        self.hoverWeapon((self.index - 1) % len(base.localAvatar.getWeapons()))

    def show(self):
        self.hoverWeapon(base.localAvatar.getActiveWeapon())
        self.root.show()
        self.isActive = True
        self.activeTime = globalClock.frame_time
        base.taskMgr.add(self.__update, 'wpnselectupdate')

    def __update(self, task):
        now = globalClock.frame_time
        if (now - self.activeTime) >= self.InactiveTime:
            self.hide()
            return task.done
        return task.cont

    def hide(self):
        self.root.hide()
        base.taskMgr.remove('wpnselectupdate')
        self.isActive = False

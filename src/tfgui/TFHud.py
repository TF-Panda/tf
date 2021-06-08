from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject

from panda3d.core import *

cl_crosshairscale = ConfigVariableDouble("cl-crosshair-scale", 32)
cl_crosshairfile = ConfigVariableString("cl-crosshair-file", "crosshair5")
cl_crosshairr = ConfigVariableDouble("cl-crosshair-r", 200)
cl_crosshairg = ConfigVariableDouble("cl-crosshair-g", 200)
cl_crosshairb = ConfigVariableDouble("cl-crosshair-b", 200)
cl_crosshaira = ConfigVariableDouble("cl-crosshair-a", 255)

class TFHud(DirectObject):

    LowHealthPerct = 0.33
    GoodHealthColor = Vec4(1, 1, 1, 1)
    LowHealthColor = Vec4(1, 0, 0, 1)

    ClipPos = (-0.15, 0.1)
    ClipAlign = TextNode.ARight
    ClipScale = 0.1

    AmmoPos = (-0.13, 0.12)
    AmmoScale = 0.07
    AmmoAlign = TextNode.ALeft

    AmmoPosNoClip = (-0.15, 0.1)
    AmmoScaleNoClip = 0.1
    AmmoAlignNoClip = TextNode.ACenter

    def __init__(self):
        self.hidden = True

        self.healthLabel = OnscreenText(text = "", fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1), parent = base.a2dBottomLeft,
                                        scale = 0.1, pos = (0.15, 0.1))

        self.clipLabel = OnscreenText(text = "", fg = (1,1, 1, 1), shadow = (0, 0, 0, 1), parent = base.a2dBottomRight,
                                      scale = self.ClipScale, pos = self.ClipPos, align = self.ClipAlign)
        self.ammoLabel = OnscreenText(text = "", fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1), parent = base.a2dBottomRight,
                                      scale = self.AmmoScale, pos = self.AmmoPos, align = self.AmmoAlign)

        self.crosshairTex = None
        self.crosshair = OnscreenImage()
        self.updateCrosshair()

        self.lastWinSize = LPoint2i(base.win.getXSize(), base.win.getYSize())
        # Accept a window event to adjust crosshair on window resize.
        self.accept('window-event', self.handleWindowEvent)

        self.hideHud()

    def hideHud(self):
        self.crosshair.hide()
        self.healthLabel.hide()
        self.clipLabel.hide()
        self.ammoLabel.hide()
        self.hidden = True

    def showHud(self):
        self.hidden = False
        self.crosshair.show()
        self.healthLabel.show()
        self.updateAmmoLabel()

    def handleWindowEvent(self, win):
        if win != base.win:
            return

        size = LPoint2i(base.win.getXSize(), base.win.getYSize())
        if size != self.lastWinSize:
            self.adjustCrosshairSize()
            self.lastWinSize = size

    def adjustCrosshairSize(self):
        factor = 32 * (base.win.getYSize() / cl_crosshairscale.getValue())
        tex = self.crosshairTex
        self.crosshair.setScale((tex.getXSize() / factor, tex.getYSize() / factor, tex.getYSize() / factor))

    def adjustCrosshairColor(self):
        self.crosshair.setTransparency(True)
        self.crosshair.setColorScale(cl_crosshairr.getValue() / 255, cl_crosshairg.getValue() / 255,
                                     cl_crosshairb.getValue() / 255, cl_crosshaira.getValue() / 255)

    def updateCrosshair(self):
        xhair_type = cl_crosshairfile.getValue()
        tex = base.loader.loadTexture(f"maps/{xhair_type}.txo")
        self.crosshairTex = tex
        self.crosshair.setImage(tex)
        self.crosshair.reparentTo(base.aspect2d)

        self.adjustCrosshairSize()
        self.adjustCrosshairColor()

    def updateHealthLabel(self):
        self.healthLabel.setText(str(base.localAvatar.health))
        hpPerct = base.localAvatar.health / base.localAvatar.maxHealth
        if hpPerct <= self.LowHealthPerct:
            self.healthLabel['fg'] = self.LowHealthColor
        else:
            self.healthLabel['fg'] = self.GoodHealthColor

    def updateAmmoLabel(self):
        if self.hidden:
            return

        if base.localAvatar.activeWeapon != -1:
            wpnId = base.localAvatar.weapons[base.localAvatar.activeWeapon]
            wpn = base.cr.doId2do.get(wpnId)

            if not wpn or (not wpn.usesAmmo):
                # Weapon invalid or doesn't use any form of ammo.

                self.ammoLabel.hide()
                self.clipLabel.hide()

            elif not wpn.usesClip:
                # Weapon doesn't use a clip.

                self.clipLabel.hide()

                self.ammoLabel.show()
                self.ammoLabel.setText(str(wpn.ammo))
                self.ammoLabel.setPos(*self.AmmoPosNoClip)
                self.ammoLabel.setAlign(self.AmmoAlignNoClip)
                self.ammoLabel.setScale(self.AmmoScaleNoClip)

            else:
                # Weapon uses clip and ammo.

                self.clipLabel.show()
                self.clipLabel.setText(str(wpn.clip))

                self.ammoLabel.show()
                self.ammoLabel.setText(str(wpn.ammo))
                self.ammoLabel.setPos(*self.AmmoPos)
                self.ammoLabel.setAlign(self.AmmoAlign)
                self.ammoLabel.setScale(self.AmmoScale)

"""CrossHairInfo module: contains the CrossHairInfo class."""

from panda3d.core import *

from tf.tfbase import TFFilters, TFGlobals
from tf.player import TFClass

from direct.gui.DirectGui import DirectFrame, OnscreenText, DGG

CTX_NONE = -1
CTX_HOVERED = 0
CTX_HEALER = 1
CTX_HEALING = 2

class InfoGui:

    def __init__(self, info):
        self.info = info
        self.frame = DirectFrame()
        self.frame.reparentTo(base.aspect2d)
        self.frame['relief'] = DGG.FLAT
        self.frame.setPos(0, 0, -0.15)
        self.elemRoot = self.frame.attachNewNode('elements')
        self.elements = {}

    def destroy(self):
        for _, elem in self.elements.items():
            elem.destroy()
        self.elements = None
        self.elemRoot.removeNode()
        self.elemRoot = None
        self.frame.destroy()
        self.frame = None
        self.info = None

    def finalizeFrame(self):
        mins = Point3()
        maxs = Point3()
        self.elemRoot.calcTightBounds(mins, maxs)
        self.frame['frameSize'] = (mins[0] - 0.03, maxs[0] + 0.03, mins[2] - 0.03, maxs[2] + 0.03)
        if self.info.ent.team == TFGlobals.TFTeam.Red:
            self.frame['frameColor'] = (0.9, 0.5, 0.5, 0.65)
        else:
            self.frame['frameColor'] = (0.5, 0.65, 1, 0.65)

class CrossHairInfo:

    def __init__(self):
        self.forceEntId = -1
        self.context = CTX_NONE
        self.ent = None
        self.gui = None

    def destroyEntInfo(self):
        if self.gui:
            self.gui.destroy()
            self.gui = None

    def buildEntInfo(self):
        self.destroyEntInfo()

        self.gui = InfoGui(self)

        font = TFGlobals.getTF2SecondaryFont()

        name = OnscreenText("", fg = (1, 1, 1, 1), shadow=(0, 0, 0, 1), font=font, parent=self.gui.elemRoot)
        if self.ent.isPlayer():
            if self.context == CTX_HOVERED:
                # Just show the name.
                name.setText(self.ent.playerName)
            elif self.context == CTX_HEALER:
                # Showing the healer's name.
                name.setText("Healer: " + self.ent.playerName)
            elif self.context == CTX_HEALING:
                # Showing who we are healing.
                name.setText("Healing: " + self.ent.playerName)
        else:
            # Object built by a player.
            name.setText(self.ent.objectName + " built by " + self.ent.getBuilder().playerName)
        self.gui.elements['name'] = name

        # Show health
        hp = OnscreenText("", fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1),
                          font=font, parent=self.gui.elemRoot, scale=0.05, pos=(0, -0.08))
        self.gui.elements['hp'] = hp

        self.maintainCurrentEnt()

    def maintainCurrentEnt(self):
        assert self.ent and self.gui

        miscInfoText = "Health: %i / %i" % (self.ent.health, self.ent.maxHealth)
        if self.ent.isPlayer():
            wpn = self.ent.getActiveWeaponObj()
            if wpn:
                # Show weapon ammo
                if wpn.usesClip and wpn.usesAmmo:
                    miscInfoText += "\nAmmo: %i / %i" % (wpn.clip, wpn.ammo)
                elif wpn.usesAmmo:
                    miscInfoText += "\nAmmo: %i" % (wpn.ammo)
            if self.ent.tfClass == TFClass.Class.Engineer:
                # Show engineer's metal amount.
                miscInfoText += "\nMetal: %i" % self.ent.metal
            elif self.ent.tfClass == TFClass.Class.Medic:
                # Show medic's charge level.
                from tf.weapon.DistributedMedigun import DistributedMedigun
                if isinstance(wpn, DistributedMedigun):
                    miscInfoText += "\nCharge: " + str(int(wpn.chargeLevel * 100)) + "%"
        else:
            # It's a building.
            # Show building level.
            miscInfoText += "\nLevel %i" % self.ent.level

        self.gui.elements['hp'].setText(miscInfoText)
        self.gui.finalizeFrame()

    def setEnt(self, ent, ctx):
        self.ent = ent
        self.context = ctx
        self.forceEntId = -1
        if self.ent:
            self.buildEntInfo()
        else:
            self.destroyEntInfo()

    def setForceEnt(self, entId, ctx):
        self.forceEntId = entId
        self.context = ctx
        self.ent = base.cr.doId2do.get(entId)
        if self.ent:
            self.buildEntInfo()

    def clearEnt(self):
        self.ent = None
        self.context = CTX_NONE
        self.forceEntId = -1
        self.destroyEntInfo()

    def findNewEnt(self):
        plyr = base.localAvatar

        src = plyr.getEyePosition()
        q = Quat()
        q.setHpr(plyr.viewAngles)
        end = src + q.getForward() * 1000000
        filter = TFFilters.TFQueryFilter(plyr)
        tr = TFFilters.traceLine(src, end, TFGlobals.Contents.Solid | TFGlobals.Contents.AnyTeam, 0, filter)
        csEnt = None
        if tr['hit'] and tr['ent']:
            ent = tr['ent']
            if ent.team == plyr.team and (ent.isPlayer() or ent.isObject()) and not ent.isDead():
                csEnt = ent

        if csEnt and csEnt == self.ent:
            self.maintainCurrentEnt()
        elif csEnt:
            self.setEnt(csEnt, CTX_HOVERED)
        else:
            self.clearEnt()

    def update(self, task):
        if base.localAvatar.isDead():
            return task.cont

        if self.forceEntId != -1:
            if not self.gui:
                self.buildEntInfo()
            else:
                self.maintainCurrentEnt()
        else:
            self.findNewEnt()

        return task.cont

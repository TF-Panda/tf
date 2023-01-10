"""CrossHairInfo module: contains the CrossHairInfo class."""

from panda3d.core import *

from tf.tfbase import TFFilters, TFGlobals, TFLocalizer, CollisionGroups
from tf.player import TFClass
from tf.object.ObjectType import ObjectType
from tf.tfgui import TFGuiProperties

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
        self.frame.setPos(0, 0, -0.2)
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
            self.frame['frameColor'] = TFGuiProperties.BackgroundColorRedTranslucent
        else:
            self.frame['frameColor'] = TFGuiProperties.BackgroundColorBlueTranslucent

class CrossHairInfo:

    def __init__(self):
        self.forceEntId = -1
        self.context = CTX_NONE
        self.ent = None
        self.gui = None

    def destroy(self):
        self.destroyEntInfo()
        self.ent = None

    def destroyEntInfo(self):
        if self.gui:
            self.gui.destroy()
            self.gui = None

    def buildEntInfo(self):
        self.destroyEntInfo()

        self.gui = InfoGui(self)

        font = TFGlobals.getTF2SecondaryFont()

        name = OnscreenText("", fg = TFGuiProperties.TextColorLight, shadow=TFGuiProperties.TextShadowColor, font=font, parent=self.gui.elemRoot)
        if self.ent.isPlayer():
            if self.context == CTX_HOVERED:
                # Just show the name.
                name.setText(self.ent.playerName)
            elif self.context == CTX_HEALER:
                # Showing the healer's name.
                name.setText(TFLocalizer.Healer + self.ent.playerName)
            elif self.context == CTX_HEALING:
                # Showing who we are healing.
                name.setText(TFLocalizer.Healing + self.ent.playerName)
        else:
            # Object built by a player.
            name.setText(self.ent.objectName + TFLocalizer.BuiltBy + self.ent.getBuilder().playerName)
        self.gui.elements['name'] = name

        self.lastText = ""

        # Show health
        hp = OnscreenText("", fg=TFGuiProperties.TextColorLight, shadow=TFGuiProperties.TextShadowColor,
                          font=font, parent=self.gui.elemRoot, scale=0.05, pos=(0, -0.08))
        self.gui.elements['hp'] = hp

        self.maintainCurrentEnt()

    def maintainCurrentEnt(self):
        assert self.ent and self.gui

        if self.ent.isDead():
            miscInfoText = TFLocalizer.Dead
        else:
            miscInfoText = TFLocalizer.HealthOutOf % (self.ent.health, self.ent.maxHealth)
            if self.ent.isPlayer():
                wpn = self.ent.getActiveWeaponObj()
                if wpn:
                    # Show weapon ammo
                    if wpn.usesClip and wpn.usesAmmo:
                        miscInfoText += TFLocalizer.AmmoOutOf % (wpn.clip, wpn.ammo)
                    elif wpn.usesAmmo:
                        miscInfoText += TFLocalizer.Ammo % (wpn.ammo)
                if self.ent.tfClass == TFClass.Class.Engineer:
                    # Show engineer's metal amount.
                    miscInfoText += TFLocalizer.Metal % self.ent.metal
                elif self.ent.tfClass == TFClass.Class.Medic:
                    # Show medic's charge level.
                    from tf.weapon.DistributedMedigun import DistributedMedigun
                    if isinstance(wpn, DistributedMedigun):
                        miscInfoText += TFLocalizer.Charge + str(int(wpn.chargeLevel * 100)) + "%"
            else:
                # It's a building.
                if not self.ent.isBuilding():
                    # Show building level.
                    miscInfoText += TFLocalizer.Level % self.ent.level
                    # If the building is less than max level, show the upgrade progress.
                    if self.ent.level < self.ent.maxLevel:
                        miscInfoText += TFLocalizer.UpgradeProgress % (self.ent.upgradeMetal, self.ent.upgradeMetalRequired)
                    if self.ent.objectType in (ObjectType.TeleporterEntrance, ObjectType.TeleporterExit):
                        # For a teleporter, show the charge level.
                        if self.ent.isTeleporterIdle():
                            if self.ent.objectType == ObjectType.TeleporterExit:
                                miscInfoText += "\n" + TFLocalizer.Entrance + " " + TFLocalizer.NotBuilt
                            else:
                                miscInfoText += "\n" + TFLocalizer.Exit + " " + TFLocalizer.NotBuilt
                        elif self.ent.isTeleporterSending():
                            miscInfoText += TFLocalizer.TeleporterSending
                        elif self.ent.isTeleporterReceiving():
                            miscInfoText += TFLocalizer.TeleporterReceiving
                        elif self.ent.isTeleporterRecharging():
                            chargeDuration = max(1, self.ent.rechargeEndTime - self.ent.rechargeStartTime)
                            chargeElapsed = max(0, base.tickCount - self.ent.rechargeStartTime)
                            chargePerct = max(0.0, min(1.0, chargeElapsed / chargeDuration))
                            miscInfoText += TFLocalizer.Charge + str(int(chargePerct * 100)) + "%"
                        else:
                            miscInfoText += TFLocalizer.ChargeFull


        if self.lastText != miscInfoText:
            self.gui.elements['hp'].setText(miscInfoText)
            self.gui.finalizeFrame()
            self.lastText = miscInfoText

    def setEnt(self, ent, ctx):
        self.ent = ent
        self.context = ctx
        self.forceEntId = -1
        if self.ent:
            self.buildEntInfo()
        else:
            self.destroyEntInfo()

    def setForceEnt(self, entId, ctx):
        if entId == -1:
            self.clearEnt()
            return

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
        tr = TFFilters.traceLine(src, end, CollisionGroups.World | CollisionGroups.Mask_AllTeam, filter)
        csEnt = None
        if tr['hit'] and tr['ent']:
            ent = tr['ent']
            if not ent.isDODisabled() and ent.team == plyr.team and (ent.isPlayer() or ent.isObject()) and not ent.isDead():
                csEnt = ent

        if csEnt and csEnt == self.ent:
            self.maintainCurrentEnt()
        elif csEnt:
            self.setEnt(csEnt, CTX_HOVERED)
        else:
            self.clearEnt()

    def update(self, task):
        #if base.localAvatar.isDead():
        #    return task.cont

        if self.forceEntId != -1:
            if self.ent:
                if self.ent.isDODisabled():
                    self.destroyEntInfo()
                    self.ent = None
                elif not self.gui:
                    self.buildEntInfo()
                else:
                    self.maintainCurrentEnt()
            else:
                self.destroyEntInfo()
        else:
            self.findNewEnt()

        return task.cont

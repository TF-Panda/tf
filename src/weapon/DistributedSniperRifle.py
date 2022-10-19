"""DistributedSniperRifle module: contains the DistributedSniperRifle class."""

from .TFWeaponGun import TFWeaponGun
from .WeaponMode import TFWeaponType, TFWeaponMode
from tf.tfbase import TFLocalizer
from tf.tfbase.TFGlobals import DamageType
from tf.player.InputButtons import InputFlag

TF_WEAPON_SNIPERRIFLE_CHARGE_PER_SEC =	50.0
TF_WEAPON_SNIPERRIFLE_UNCHARGE_PER_SEC =	75.0
TF_WEAPON_SNIPERRIFLE_DAMAGE_MIN =		50
TF_WEAPON_SNIPERRIFLE_DAMAGE_MAX =		150
TF_WEAPON_SNIPERRIFLE_RELOAD_TIME =		1.5
TF_WEAPON_SNIPERRIFLE_ZOOM_TIME =			0.3

class DistributedSniperRifle(TFWeaponGun):

    WeaponModel = "models/weapons/w_sniperrifle"
    WeaponViewModel = "models/weapons/v_sniperrifle_sniper"
    UsesViewModel = True

    def __init__(self):
        TFWeaponGun.__init__(self)
        self.weaponType = TFWeaponType.Primary
        self.weaponData[TFWeaponMode.Primary].update({
            'damage': 4,
            'range': 8192,
            'bulletsPerShot': 1,
            'spread': 0.0,
            'timeFireDelay': 1.5
        })
        self.usesClip = False
        self.maxAmmo = 25
        self.ammo = self.maxAmmo
        self.damageType = DamageType.Bullet | DamageType.UseHitLocations

        self.resetTimers()
        self.chargedDamage = 0.0

    def getName(self):
        return TFLocalizer.SniperRifle

    def getSingleSound(self):
        return "Weapon_SniperRifle.Single"

    def getEmptySound(self):
        return "Weapon_SniperRifle.ClipEmpty"

    def getReloadSound(self):
        return "Weapon_SniperRifle.WorldReload"

    if IS_CLIENT:
        def addPredictionFields(self):
            TFWeaponGun.addPredictionFields(self)
            self.addPredictionField("unzoomTime", float, networked=False)
            self.addPredictionField("rezoomTime", float, networked=False)
            self.addPredictionField("rezoomAfterShot", bool, networked=False)
            self.addPredictionField("chargedDamage", float, networked=True, tolerance=0.01)

    def resetTimers(self):
        self.unzoomTime = -1
        self.rezoomTime = -1
        self.rezoomAfterShot = False

    def reload(self):
        return True

    def canDeactivate(self):
        #if self.player:
        return True

    def deactivate(self):
        if self.player and self.player.inCondition(self.player.CondZoomed):
            self.zoomOut()

        self.chargedDamage = 0.0
        self.resetTimers()

        TFWeaponGun.deactivate(self)

    def weaponReset(self):
        #TFWeaponGun.weaponReset(self)
        self.zoomOut()

    def handleZooms(self):
        if not self.player:
            return

        if self.player.inCondition(self.player.CondTaunting):
            if self.player.inCondition(self.player.CondAiming):
                self.toggleZoom()

            self.resetTimers()

        if self.unzoomTime > 0 and globalClock.frame_time > self.unzoomTime:
            if self.rezoomAfterShot:
                self.zoomOutIn()
                self.rezoomAfterShot = False
            else:
                self.zoomOut()

            self.unzoomTime = -1

        if self.rezoomTime > 0:
            if globalClock.frame_time > self.rezoomTime:
                self.zoomIn()
                self.rezoomTime = -1

        if (self.player.buttons & InputFlag.Attack2) and self.nextSecondaryAttack <= globalClock.frame_time:
            # If we're in the process of rezooming, just cancel it.
            if self.rezoomTime > 0 or self.unzoomTime > 0:
                # Prevent them from rezooming in less time than they would have
                self.nextSecondaryAttack = self.rezoomTime + TF_WEAPON_SNIPERRIFLE_ZOOM_TIME
                self.rezoomTime = -1
            else:
                self.zoom()

    def itemPostFrame(self):
        if not self.player:
            return

        #if not self.canAttack():
        # if self.isZoomed():
        #  self.toggleZoom()
        # return

        self.handleZooms()

        # Start charging when we're zoomed in, and allowed to fire
        if not self.player.onGround:
            # Unzoom if we're off the ground.
            if self.isZoomed():
                self.toggleZoom()

            self.chargedDamage = 0.0
            self.rezoomAfterShot = False
        elif self.nextSecondaryAttack <= globalClock.frame_time:
            # Don't start charging in the time just after a shot before
            # we unzoom to play rack anim.
            if self.player.inCondition(self.player.CondAiming) and not self.rezoomAfterShot:
                self.chargedDamage = min(self.chargedDamage + globalClock.dt * TF_WEAPON_SNIPERRIFLE_CHARGE_PER_SEC, TF_WEAPON_SNIPERRIFLE_DAMAGE_MAX)
            else:
                self.chargedDamage = max(0, self.chargedDamage - globalClock.dt * TF_WEAPON_SNIPERRIFLE_UNCHARGE_PER_SEC)

        # Fire
        if self.player.buttons & InputFlag.Attack1:
            self.fire(self.player)

        # Idle.
        if not (self.player.buttons & (InputFlag.Attack1 | InputFlag.Attack2)):
            # No fire buttons or reloading.
            if not self.reloadOrSwitchWeapons() and not self.inReload:
                self.weaponIdle()

    def zoom(self):
        if not self.player.onGround:
            # Don't allow the player to zoom in while in air.
            if self.player.fov >= 75:
                return

        self.toggleZoom()

        # At least 0.1 seconds from now, but don't stomp a previous value
        self.nextPrimaryAttack = max(self.nextPrimaryAttack, globalClock.frame_time + 0.1)
        self.nextSecondaryAttack = globalClock.frame_time + TF_WEAPON_SNIPERRIFLE_ZOOM_TIME

    def zoomOutIn(self):
        self.zoomOut()

        if self.player and self.player.autoRezoom:
            self.rezoomTime = globalClock.frame_time + 0.9
        else:
            self.nextSecondaryAttack = globalClock.frame_time + 1.0

    def zoomIn(self):
        # Start aiming.
        if self.ammo <= 0:
            return

        self.player.setFOV(20, 0.1)
        self.player.setCondition(self.player.CondZoomed)

        self.player.setCondition(self.player.CondAiming)
        self.player.updateClassSpeed()

    def isZoomed(self):
        return self.player.inCondition(self.player.CondZoomed)

    def getWeaponDamage(self):
        return max(self.chargedDamage, TF_WEAPON_SNIPERRIFLE_DAMAGE_MIN)

    def zoomOut(self):
        #if self.player.inCondition(self.player.CondZoomed):
        self.player.setFOV(0, 0.1)
        self.player.removeCondition(self.player.CondZoomed)

        self.player.removeCondition(self.player.CondAiming)
        self.player.updateClassSpeed()

        # If we're thinking about zooming, cancel it
        self.resetTimers()
        self.chargedDamage = 0.0

    def toggleZoom(self):
        if self.player.fov >= 75:
            self.zoomIn()
        else:
            self.zoomOut()
        self.nextSecondaryAttack = globalClock.frame_time + 1.2

    def fire(self, player):
        if self.ammo <= 0:
            self.handleFireOnEmpty()
            return

        if self.nextPrimaryAttack > globalClock.frame_time:
            return

        self.primaryAttack()

        if self.isZoomed():
            # If we have more bullets, zoom out, play the bolt animation and zoom back in.
            if self.ammo > 0:
                self.setRezoom(True, 0.5) # Zoom out in 0.5 seconds, then rezoom
            else:
                # Just zoom out in 0.5 seconds
                self.setRezoom(False, 0.5)
        else:
            # Prevent primary fire preventing zooms
            self.nextSecondaryAttack = globalClock.frame_time + self.viewModel.getCurrentAnimLength()

        self.chargedDamage = 0.0

    def setRezoom(self, rezoom, delay):
        self.unzoomTime = globalClock.frame_time + delay
        self.rezoomAfterShot = rezoom

if not IS_CLIENT:
    DistributedSniperRifleAI = DistributedSniperRifle
    DistributedSniperRifleAI.__name__ = 'DistributedSniperRifleAI'

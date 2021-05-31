
from tf.character.Char import Char

class DistributedWeaponShared:

    WeaponModel = None
    WeaponViewModel = None

    def __init__(self):
        self.ammo = 0
        self.ammo2 = 0
        self.maxAmmo = 0
        self.maxAmmo2 = 0
        self.clip = 0
        self.clip2 = 0
        self.maxClip = 0
        self.maxClip2 = 0
        self.playerId = -1
        # Player DO
        self.player = None
        # ViewModel DO
        self.viewModel = None

        self.viewModelChar = None

        # Do we use a clip at all?  Would be true for the pistol, shotgun, etc,
        # false for the minigun.
        self.usesClip = True
        self.usesClip2 = False

        # If true, increments the clip one by one when reloading, otherwise the
        # entire clip is refilled at once when reloading.
        self.reloadsSingly = False

        # Do we use ammo at all?  Would be false for things like melee weapons.
        self.usesAmmo = True
        self.usesAmmo2 = False

        # When are we allowed to primary attack next?
        self.nextPrimaryAttack = 0.0
        self.nextSecondaryAttack = 0.0

        self.nextEmptySoundTime = 0.0

        # Currently reloading?
        self.inReload = False

        self.meleeWeapon = False

        self.fireDuration = 0.0

        self.timeWeaponIdle = 0.0

        self.lowered = False

    def getName(self):
        return "weapon_name"

    def getSingleSound(self):
        return ""

    def getEmptySound(self):
        return ""

    def itemPreFrame(self):
        pass

    def itemPostFrame(self):
        pass

    def generate(self):
        self.viewModelChar = Char()
        self.viewModelChar.loadModel(self.WeaponViewModel)

    def delete(self):
        self.viewModelChar.cleanup()
        self.viewModelChar = None
        self.player = None
        self.viewModel = None

    def getAmmo(self):
        return self.ammo

    def getMaxAmmo(self):
        return self.maxAmmo

    def getClip(self):
        return self.clip

    def getMaxClip(self):
        return self.maxClip

if IS_CLIENT:
    from .TFWeapon import TFWeapon
    BaseClass = TFWeapon
else:
    from .TFWeapon import TFWeaponAI
    BaseClass = TFWeaponAI

from panda3d.core import *
from panda3d.pphysics import *

from .WeaponMode import TFWeaponMode, TFReloadMode, TFProjectileType
from tf.character.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from .FireBullets import fireBullets

from tf.tfbase.TFGlobals import CollisionGroup, Contents
from tf.tfbase import TFFilters

from tf.character.Char import Char

if not IS_CLIENT:
    from .RocketProjectile import RocketProjectileAI

class TFWeaponGun(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        self.weaponMode = TFWeaponMode.Primary

    def primaryAttack(self):

        # Check for ammunition.
        if self.clip <= 0 and self.clip != -1:
            return

        # Are we capable of firing again.
        if self.nextPrimaryAttack > globalClock.getFrameTime():
            return

        # Get the player owning the weapon.
        player = self.player
        if not player:
            return

        #if not self.canAttack():
        #    return

        #self.calcIsAttackCritical()

        #if not IS_CLIENT:
        #    pass # TODO: remove invisibility/disguise, speak weapon fire

        # Set the weapon mode
        self.weaponMode = TFWeaponMode.Primary

        self.sendWeaponAnim(Activity.VM_Fire)
        player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)
        self.fireProjectile(player)

        # Set next attack times
        self.nextPrimaryAttack = globalClock.getFrameTime() + self.primaryAttackInterval

        self.timeWeaponIdle = globalClock.getFrameTime() + self.getVMSequenceLength()

        # Check the reload mode and behave appriopriately
        if self.reloadsSingly:
            self.reloadMode = TFReloadMode.Start

        if not IS_CLIENT:
            self.player.sendUpdate('makeAngry')

    def secondaryAttack(self):
        if self.inAttack2:
            return

        self.player.doClassSpecialSkill()
        self.inAttack2 = True
        self.nextSecondaryAttack = globalClock.getFrameTime() + 0.5

    def fireProjectile(self, player):
        self.syncAllHitBoxes()

        projType = self.weaponData[self.weaponMode]['projectile']

        if projType == TFProjectileType.Bullet:
            self.fireBullet(player)
        elif projType == TFProjectileType.Rocket:
            self.fireRocket(player)
        else:
            assert False

        if self.clip != -1:
            self.clip -= self.weaponData[self.weaponMode]['ammoPerShot']
        else:
            self.ammo -= self.weaponData[self.weaponMode]['ammoPerShot']

        self.doFireEffects()
        self.updatePunchAngles(player)

    def doFireEffects(self):
        pass

    def updatePunchAngles(self, player):
        pass

    def getProjectileFireSetup(self, player, offset, hitTeammates = True):
        q = Quat()
        q.setHpr(player.viewAngles)
        forward = q.getForward()
        right = q.getRight()
        up = q.getUp()
        shootPos = player.getEyePosition()

        # Estimate end point
        endPos = shootPos + forward * 2000

        dir = endPos - shootPos
        dist = dir.length()
        dir.normalize()

        # Trace forward and find what's in front of us, and aim at that.

        if hitTeammates:
            filter = PhysQueryNodeFilter(player, PhysQueryNodeFilter.FTExclude)
        else:
            filter = TFFilters.TFQueryFilter(player, [TFFilters.ignoreTeammates])
        res = PhysRayCastResult()
        base.physicsWorld.raycast(res, shootPos, dir, dist, Contents.Solid | Contents.AnyTeam,
                                  Contents.Empty, CollisionGroup.Empty, filter)
        if res.hasBlock():
            b = res.getBlock()
            end = b.getPosition()
            frac = (end - shootPos).length() / dist
        else:
            end = endPos
            frac = 1.0

        # Offset actual start point.
        src = shootPos + (forward * offset.x) + (right * offset.y) + (up * offset.z)

        # Find angles that will get us to our desired end point.
        # Only use the trace end if it wasn't too close, which results
        # in visually bizarre forward angles
        q = Quat()
        if frac > 0.1:
            lookAt(q, end - src)
        else:
            lookAt(q, endPos - src)

        return (src, q)

    def fireRocket(self, player):
        self.playSound(self.getSingleSound())
        # Server only -- create the rocket.
        if not IS_CLIENT:
            offset = Vec3(23.5, 12.0, -3.0)
            # TODO: if is ducking offset z = 8.0
            src, q = self.getProjectileFireSetup(player, offset)
            rocket = RocketProjectileAI()
            rocket.setPos(src)
            rocket.setQuat(q)
            rocket.shooter = player
            rocket.damage = self.weaponData[self.weaponMode]['damage']
            rocket.damageType = self.damageType
            base.net.generateObject(rocket, player.zoneId)

    def fireBullet(self, player):
        self.playSound(self.getSingleSound())
        weaponData = self.weaponData.get(self.weaponMode, {})
        origin = self.player.getEyePosition()
        angles = self.player.viewAngles
        fireBullets(self.player, origin, angles, self,
                    self.weaponMode,
                    base.net.predictionRandomSeed & 255,
                    weaponData.get('spread', 0.0),
                    weaponData.get('damage', 1.0))

if not IS_CLIENT:
    TFWeaponGunAI = TFWeaponGun
    TFWeaponGunAI.__name__ = 'TFWeaponGunAI'

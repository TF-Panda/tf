if IS_CLIENT:
    from .TFWeapon import TFWeapon
    BaseClass = TFWeapon
else:
    from .TFWeapon import TFWeaponAI
    BaseClass = TFWeaponAI

from panda3d.core import *
from panda3d.pphysics import *

from tf.actor.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.tfbase import CollisionGroups, TFFilters, TFGlobals

from .FireBullets import fireBullets
from .WeaponEffects import makeMuzzleFlash
from .WeaponMode import TFProjectileType, TFReloadMode, TFWeaponMode

if not IS_CLIENT:
    from .RocketProjectile import RocketProjectileAI
    from .DPipeBombProjectile import DPipeBombProjectileAI
    from .DistributedStickyBomb import DistributedStickyBombAI

import random


class TFWeaponGun(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)
        self.weaponMode = TFWeaponMode.Primary
        self.staggerTracers = False
        self.tracerSpread = 0.0

    def speakWeaponFire(self):
        pass

    def primaryAttack(self):

        # Check for ammunition.
        if self.clip <= 0 and self.usesClip:
            return

        # Are we capable of firing again.
        if self.nextPrimaryAttack > base.clockMgr.getTime():
            return

        # Get the player owning the weapon.
        player = self.player
        if not player:
            return

        #if not self.canAttack():
        #    return

        #self.calcIsAttackCritical()

        if not IS_CLIENT:
            # TODO: remove invisibility/disguise
            self.speakWeaponFire()

        # Set the weapon mode
        self.weaponMode = TFWeaponMode.Primary

        self.sendWeaponAnim(Activity.VM_Fire)
        player.doAnimationEvent(PlayerAnimEvent.AttackPrimary)
        self.fireProjectile(player)

        # Set next attack times
        self.nextPrimaryAttack = base.clockMgr.getTime() + self.primaryAttackInterval

        self.timeWeaponIdle = base.clockMgr.getTime() + self.getVMSequenceLength()

        # Check the reload mode and behave appriopriately
        if self.reloadsSingly:
            self.reloadMode = TFReloadMode.Start

        if not IS_CLIENT:
            self.player.pushExpression('specialAction')

    def secondaryAttack(self):
        if self.inAttack2:
            return

        self.player.doClassSpecialSkill()
        self.inAttack2 = True
        self.nextSecondaryAttack = base.clockMgr.getTime() + 0.5

    def fireProjectile(self, player):
        self.syncAllHitBoxes()

        projType = self.weaponData[self.weaponMode]['projectile']

        if projType == TFProjectileType.Bullet:
            self.fireBullet(player)
        elif projType == TFProjectileType.Rocket:
            self.fireRocket(player)
        elif projType == TFProjectileType.Pipebomb:
            self.firePipebomb(player)
        elif projType == TFProjectileType.PipebombRemote:
            self.fireStickyBomb(player)
        else:
            assert False

        if self.usesClip:
            self.clip -= self.weaponData[self.weaponMode]['ammoPerShot']
        else:
            self.ammo -= self.weaponData[self.weaponMode]['ammoPerShot']

        self.doFireEffects()
        self.updatePunchAngles(player)

    def doFireEffects(self):
        if self.HideWeapon:
            return

        if IS_CLIENT:
            if self.isOwnedByLocalPlayer():
                if base.cr.prediction.hasBeenPredicted():
                    return
                # Get the muzzle from the view model weapon.
                if self.UsesViewModel:
                    muzzle = self.player.viewModel.find("**/muzzle")
                else:
                    muzzle = self.viewModelChar.modelNp.find("**/muzzle")
                isViewModel = True
            else:
                # World model.
                muzzle = self.find("**/muzzle")
                isViewModel = False
            if not muzzle.isEmpty():
                makeMuzzleFlash(muzzle, (0, 0, 0), (0, 0, 0), 1.0, (1, 0.75, 0, 1), isViewModel)
        else:
            # Don't send to owner, who is predicting the effect.
            self.sendUpdate('doFireEffects', excludeClients = [self.player.owner])

    def updatePunchAngles(self, player):
        player.resetViewPunch()
        punchAngle = self.weaponData[self.weaponMode].get('punchAngle', 0)
        if punchAngle > 0:
            rand = random.Random()
            rand.seed(base.net.predictionRandomSeed & 255)
            player.punchAngle[1] += rand.randint(int(punchAngle - 1), int(punchAngle + 1))
           # print("applied punch angle, it's now", player.punchAngle)
            #print("pred tick", base.tickCount)
            #print("random seed", base.net.predictionRandomSeed & 255)

    def getProjectileFireSetup(self, player, offset, hitTeammates = True, shootPos=None):
        q = Quat()
        q.setHpr(player.viewAngles)
        forward = q.getForward()
        right = q.getRight()
        up = q.getUp()
        if not shootPos:
            shootPos = player.getEyePosition()

        # Estimate end point
        endPos = shootPos + forward * 2000

        dir = endPos - shootPos
        dist = dir.length()
        dir.normalize()

        # Trace forward and find what's in front of us, and aim at that.

        mask = CollisionGroups.World
        if hitTeammates:
            mask |= CollisionGroups.Mask_AllTeam
        else:
            mask |= CollisionGroups.Mask_Blue if self.team == TFGlobals.TFTeam.Red else CollisionGroups.Mask_Red

        filter = TFFilters.TFQueryFilter(player)
        tr = TFFilters.traceLine(shootPos, endPos, mask, filter)

        # Offset actual start point.
        src = shootPos + (forward * offset.x) + (right * offset.y) + (up * offset.z)

        # Find angles that will get us to our desired end point.
        # Only use the trace end if it wasn't too close, which results
        # in visually bizarre forward angles
        q = Quat()
        if tr['frac'] > 0.1:
            lookAt(q, tr['endpos'] - src)
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

    def firePipebomb(self, player):
        self.playSound(self.getSingleSound())
        # Server only -- create the rocket.
        if not IS_CLIENT:
            src = self.player.getEyePosition()
            q = Quat()
            q.setHpr(self.player.viewAngles)
            src += q.getForward() * 16.0 + q.getRight() * 8.0 + q.getUp() * -6.0
            vel = (q.getForward() * 1200) + (q.getUp() * 200.0) + (q.getRight() * random.uniform(-10.0, 10.0)) + (q.getUp() * random.uniform(-10.0, 10.0))
            rocket = DPipeBombProjectileAI()
            rocket.setPos(src)
            rocket.setHpr(self.player.viewAngles)
            rocket.shooter = player
            rocket.fullDamage = self.weaponData[self.weaponMode]['damage']
            rocket.damage = rocket.fullDamage * 0.6
            rocket.damageType = self.damageType
            rocket.team = self.player.team
            rocket.skin = TFGlobals.getTeamSkin(self.player.team)
            # Material for grenade comes from surfaceproperties now.
            rocket.setModel("models/weapons/w_grenade_grenadelauncher")
            #physMat = PhysMaterial(0.6, 0.2, 0.2)
            #rocket.node().getShape(0).setMaterial(physMat)
            rocket.node().addForce(vel, rocket.node().FTVelocityChange)
            rocket.node().addTorque((random.uniform(-1200, 1200), -600, 0), rocket.node().FTVelocityChange)
            rocket.node().setCcdEnabled(True)
            rocket.node().setMass(5.0)
            base.net.generateObject(rocket, player.zoneId)

    def fireStickyBomb(self, player):
        self.playSound(self.getSingleSound())
        if not IS_CLIENT:
            src = self.player.getEyePosition()
            q = Quat()
            q.setHpr(self.player.viewAngles)
            src += q.getForward() * 16.0 + q.getRight() * 8.0 + q.getUp() * -6.0
            vel = (q.getForward() * 1200) + (q.getUp() * 200.0)
            vel *= TFGlobals.remapValClamped(self.charge, 0.0, 1.0, 0.8, 1.5)
            bomb = DistributedStickyBombAI()
            bomb.setPos(src)
            bomb.setHpr(self.player.viewAngles)
            bomb.shooter = player
            bomb.damage = self.getWeaponDamage()
            bomb.damageType = self.getWeaponDamageType()
            bomb.team = player.team
            bomb.skin = TFGlobals.getTeamSkin(bomb.team)
            bomb.setModel("models/weapons/w_stickybomb")
            bomb.node().addForce(vel, bomb.node().FTVelocityChange)
            bomb.node().addTorque((random.uniform(-1200, 1200), -600, 0), bomb.node().FTVelocityChange)
            bomb.node().setCcdEnabled(True)
            bomb.node().setMass(150.0)
            base.net.generateObject(bomb, player.zoneId)
            player.addDetonateable(bomb)

    def getWeaponDamage(self):
        return self.weaponData.get(self.weaponMode, {}).get('damage', 1.0)

    def getWeaponDamageType(self):
        return self.damageType

    def fireBullet(self, player):
        self.playSound(self.getSingleSound())
        weaponData = self.weaponData.get(self.weaponMode, {})
        origin = self.player.getEyePosition()
        angles = self.player.viewAngles
        fireBullets(self.player, origin, angles, self,
                    self.weaponMode,
                    base.net.predictionRandomSeed & 255,
                    weaponData.get('spread', 0.0),
                    self.getWeaponDamage(),
                    tracerAttachment="muzzle",
                    tracerStagger=(self.primaryAttackInterval / weaponData.get('bulletsPerShot', 1)) if self.staggerTracers else 0.0,
                    tracerSpread=self.tracerSpread)

if not IS_CLIENT:
    TFWeaponGunAI = TFWeaponGun
    TFWeaponGunAI.__name__ = 'TFWeaponGunAI'

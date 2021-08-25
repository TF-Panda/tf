
from panda3d.core import Vec3, Quat, lookAt, Filename
from panda3d.direct import InterpolatedFloat

from .BaseObject import BaseObject

from tf.character.Activity import Activity
from tf.tfbase import TFGlobals
from tf.tfbase.TFGlobals import Contents, DamageType

from .ObjectState import ObjectState
from .ObjectType import ObjectType

import random
from enum import IntEnum

# Only means anything when object is active.
class SentryState(IntEnum):
    Inactive = 0
    Searching = 1
    Attacking = 2

SENTRYGUN_EYE_OFFSET_LEVEL_1 = Vec3(0, 0, 32)
SENTRYGUN_EYE_OFFSET_LEVEL_2 = Vec3(0, 0, 40)
SENTRYGUN_EYE_OFFSET_LEVEL_3 = Vec3(0, 0, 46)
SENTRYGUN_MAX_SHELLS_1 = 100
SENTRYGUN_MAX_SHELLS_2 = 120
SENTRYGUN_MAX_SHELLS_3 = 144
SENTRYGUN_MAX_ROCKETS = 20
SENTRYGUN_BUILD_COST = 130
SENTRYGUN_UPGRADE_METAL = 200
SENTRYGUN_HEALTH_1 = 150
SENTRYGUN_HEALTH_2 = 180
SENTRYGUN_HEALTH_3 = 216

metal_per_shell = 1
metal_per_rocket = 2

# Layer for bullet firing gesture.
SENTRYGUN_BULLET_ANIM_LAYER = 1
# Layer for rocket firing gesture.
SENTRYGUN_ROCKET_ANIM_LAYER = 2

class SentryGun(BaseObject):

    def __init__(self):
        BaseObject.__init__(self)
        self.objectType = ObjectType.SentryGun
        self.goalAngles = Vec3()
        self.currAngles = Vec3()
        self.turningRight = False
        self.leftBound = 315
        self.rightBound = 45
        self.baseTurnRate = 6
        self.turnRate = 0
        self.lookPitch = 0.5
        self.lookYaw = 0.5
        self.sentryState = SentryState.Inactive
        self.nextAttack = 0.0
        self.lastAttackedTime = 0.0
        self.nextRocketAttack = 0.0
        self.maxHealth = SENTRYGUN_HEALTH_1
        self.health = self.maxHealth
        self.ammoShells = SENTRYGUN_MAX_SHELLS_1
        self.maxAmmoShells = self.ammoShells
        self.numRockets = SENTRYGUN_MAX_ROCKETS
        self.maxRockets = self.numRockets
        self.viewOffset = SENTRYGUN_EYE_OFFSET_LEVEL_1
        self.numKills = 0
        self.numAssists = 0
        if IS_CLIENT:
            self.ivPitch = InterpolatedFloat()
            self.addInterpolatedVar(self.ivPitch, self.getLookPitch, self.setLookPitch)
            self.ivYaw = InterpolatedFloat()
            self.ivYaw.setLooping(True)
            self.addInterpolatedVar(self.ivYaw, self.getLookYaw, self.setLookYaw)
        self.enemy = None

        self.maxLevel = 2

    if not IS_CLIENT:

        def onKilled(self, killer):
            bldr = self.getBuilder()
            if bldr:
                bldr.d_speak("Engineer.AutoDestroyedSentry01")
            BaseObject.onKilled(self, killer)

        def onKillEntity(self, ent):
            # Don't count killing the engineer.
            if ent.doId != self.builderDoId:
                self.numKills += 1

        def onWrenchHit(self, player):
            didWork = BaseObject.onWrenchHit(self, player)
            if not self.isUpgrading():
                playerMetal = 200 #TODO
                # If the sentry has less than 100% ammo, put some ammo in it
                if self.ammoShells < self.maxAmmoShells and playerMetal > 0:
                    maxShellsCanAfford = int(playerMetal / metal_per_shell)
                    # Cap to the amount we can add
                    amountToAdd = min(40, maxShellsCanAfford)
                    amountToAdd = min(self.maxAmmoShells - self.ammoShells, amountToAdd)
                    # TODO: remove metal
                    self.ammoShells += amountToAdd
                    if amountToAdd > 0:
                        didWork = True

                # TODO: one rocket per two ammo
            return didWork

        def onUpgrade(self):
            if self.level == 2:
                self.setModel("tfmodels/src/buildables/sentry2_heavy.pmdl")
                self.viewOffset = SENTRYGUN_EYE_OFFSET_LEVEL_2
                self.maxAmmoShells = SENTRYGUN_MAX_SHELLS_2
            elif self.level == 3:
                self.setModel("tfmodels/src/buildables/sentry3_heavy.pmdl")
                self.viewOffset = SENTRYGUN_EYE_OFFSET_LEVEL_3
                self.maxAmmoShells = SENTRYGUN_MAX_SHELLS_3

            # More shells
            self.ammoShells = self.maxAmmoShells

        def generate(self):
            self.setModel("tfmodels/src/buildables/sentry1.pmdl")
            BaseObject.generate(self)

        def onFinishUpgrade(self):
            self.sentryState = SentryState.Searching
            self.enemy = None
            if self.level == 2:
                self.setModel("tfmodels/src/buildables/sentry2.pmdl")
            elif self.level == 3:
                self.setModel("tfmodels/src/buildables/sentry3.pmdl")
            self.emitSound("Building_Sentrygun.Built")

        def onFinishConstruction(self):
            self.emitSound("Building_Sentrygun.Built")

        def onBecomeActive(self):
            if self.level > 1:
                # Only do this when the sentry just finished initial
                # construction.
                return

            # Orient it
            angles = self.getHpr()
            self.currAngles.x = TFGlobals.angleMod(angles.x)
            self.rightBound = TFGlobals.angleMod(int(angles.x - 50))
            self.leftBound = TFGlobals.angleMod(int(angles.x + 50))
            if self.rightBound > self.leftBound:
                self.rightBound = self.leftBound
                self.leftBound = TFGlobals.angleMod(int(angles.x - 50))

            # Start rotating it
            self.goalAngles.x = self.rightBound
            self.goalAngles.y = self.currAngles.y = 0.0
            self.turningRight = True

            self.sentryState = SentryState.Searching

        def simulateActive(self):
            if self.sentryState == SentryState.Searching:
                self.sentryRotate()
            elif self.sentryState == SentryState.Attacking:
                self.attack()

        def moveTurret(self):
            moved = False

            baseTurnRate = self.baseTurnRate

            if self.currAngles.y != self.goalAngles.y:
                dir = 1 if self.goalAngles.y > self.currAngles.y else -1

                self.currAngles.y += globalClock.getDt() * (baseTurnRate * 5) * dir

                # If we started below the goal, and now we're past, peg to goal.
                if dir == 1:
                    if self.currAngles.y > self.goalAngles.y:
                        self.currAngles.y = self.goalAngles.y
                else:
                    if self.currAngles.y < self.goalAngles.y:
                        self.currAngles.y = self.goalAngles.y

                pp = self.getPoseParameter("aim_pitch")
                if pp:
                    #print("Aim pitch", -self.currAngles.y)
                    pp.setValue(-self.currAngles.y)
                    self.lookPitch = pp.getNormValue()

                moved = True

            if self.currAngles.x != self.goalAngles.x:
                dir = 1 if self.goalAngles.x > self.currAngles.x else -1
                dist = abs(self.goalAngles.x - self.currAngles.x)
                reversed = False

                if dist > 180:
                    dist = 360 - dist
                    dir = -dir
                    reversed = True

                if not self.enemy:
                    if dist > 30:
                        if self.turnRate < baseTurnRate * 10:
                            self.turnRate += baseTurnRate
                    else:
                        # Slow down
                        if self.turnRate > (baseTurnRate * 5):
                            self.turnRate -= baseTurnRate
                else:
                    # When tracking enemies, move faster and don't slow.
                    if dist > 30:
                        if self.turnRate < baseTurnRate * 30:
                            self.turnRate += baseTurnRate * 3

                self.currAngles.x += globalClock.getDt() * self.turnRate * dir

                # If we passed over the goal, peg right to it now
                if dir == -1:
                    if (not reversed and self.goalAngles.x > self.currAngles.x) or \
                        (reversed and self.goalAngles.x < self.currAngles.x):
                        self.currAngles.x = self.goalAngles.x
                else:
                    if (not reversed and self.goalAngles.x < self.currAngles.x) or \
                        (reversed and self.goalAngles.x > self.currAngles.x):
                        self.currAngles.x = self.goalAngles.x

                if self.currAngles.x < 0:
                    self.currAngles.x += 360
                elif self.currAngles.x >= 360:
                    self.currAngles.x -= 360

                if dist < (globalClock.getDt() * 0.5 * baseTurnRate):
                    self.currAngles.x = self.goalAngles.x

                angles = self.getHpr()
                yaw = self.currAngles.x - angles.x
                pp = self.getPoseParameter("aim_yaw")
                if pp:
                    #print("Aim yaw", -yaw)
                    pp.setValue(-yaw)
                    self.lookYaw = pp.getNormValue()

                moved = True

            if not moved or (self.turnRate <= 0):
                self.turnRate = baseTurnRate * 5

            return moved

        def isValidTargetPlayer(self, player, sentryOrigin, targetCenter):
            # TODO: spies invisible pct

            # TODO: disguised spies

            # TODO: not cross water boundary

            # Ray trace!!!
            return self.isEntityVisible(player, Contents.Solid | Contents.HitBox)

        def isValidTargetObject(self, obj, sentryOrigin, targetCenter):
            # TODO: is placing

            # TODO: ignore sappers

            # TODO: not cross water boundary

            # Ray trace
            return self.isEntityVisible(obj, Contents.Solid | Contents.HitBox)

        def foundTarget(self, target, soundCenter):
            self.enemy = target
            if (self.ammoShells > 0) or (self.numRockets > 0 and self.level == 3):
                # Play one sound to everyone but the target.
                if target.__class__.__name__ == 'DistributedTFPlayerAI':
                    # Play a specific sound just to the target.
                    self.emitSound("Building_Sentrygun.AlertTarget", client=target.owner)
                self.emitSound("Building_Sentrygun.Alert", excludeClients=[target.owner])

            # Update timers, we are attacking now!
            self.sentryState = SentryState.Attacking
            self.nextAttack = globalClock.getFrameTime()
            if self.nextRocketAttack < globalClock.getFrameTime():
                self.nextRocketAttack = globalClock.getFrameTime() + 0.5

        def attack(self):
            self.character.update()

            if not self.findTarget():
                # Lost target.
                self.sentryState = SentryState.Searching
                self.enemy = None
                return

            # Track enemy
            mid = self.getEyePosition()
            midEnemy = self.enemy.getEyePosition()
            dirToEnemy = midEnemy - mid
            q = Quat()
            lookAt(q, dirToEnemy)
            angToTarget = q.getHpr()

            angToTarget.x = TFGlobals.angleMod(angToTarget.x)
            if angToTarget.y < -180:
                angToTarget.y += 360
            if angToTarget.y > 180:
                angToTarget.y -= 360

            # Now all numbers should be in [1..360]
            # Pin to turret limitations [-50..50]
            if angToTarget.y > 50:
                angToTarget.y = 50
            elif angToTarget.y < -50:
                angToTarget.y = -50
            self.goalAngles.y = -angToTarget.y
            self.goalAngles.x = angToTarget.x

            self.moveTurret()

            # Fire on the target if it's within 10 units of being aimed right at it.
            if self.nextAttack <= globalClock.getFrameTime() and (self.goalAngles - self.currAngles).length() <= 10:
                self.fire()

                if self.level == 1:
                    # Level 1 sentries fire slower.
                    self.nextAttack = globalClock.getFrameTime() + 0.2
                else:
                    self.nextAttack = globalClock.getFrameTime() + 0.1

        def fire(self):
            aimDir = Vec3()

            # TODO: Fire rockets lvl 3

            # All turrets fire shells
            if self.ammoShells > 0:
                self.startChannel(act = Activity.Object_Fire, layer = SENTRYGUN_BULLET_ANIM_LAYER, restart = False)

                if self.level > 1 and (self.ammoShells & 1):
                    # level 2 and 3 turrets alternate muzzles each time they fizzy fizzy fire.
                    trans = self.character.getAttachmentNetTransform(1)
                else:
                    trans = self.character.getAttachmentNetTransform(0)

                src = trans.getPos()
                #ang = trans.getHpr()

                midEnemy = self.enemy.getEyePosition() - (0, 0, 5)
                aimDir = midEnemy - src
                distToTarget = aimDir.length()
                aimDir.normalize()

                info = {
                    'shots': 1,
                    'spread': Vec3(),
                    'tracerFreq': 1,
                    'src': src,
                    'damage': 16,
                    'dirShooting': aimDir,
                    'attacker': self.getBuilder(),
                    'distance': distToTarget + 100,
                    'damageType': DamageType.Bullet
                }
                self.fireBullets(info)

                if self.level == 1:
                    self.emitSound("Building_Sentrygun.Fire")
                elif self.level == 2:
                    self.emitSound("Building_Sentrygun.Fire2")
                elif self.level == 3:
                    self.emitSound("Building_Sentrygun.Fire3")

                self.ammoShells -= 1
            else:
                self.startChannel(act = Activity.Object_Fire_Empty,
                                  layer = SENTRYGUN_BULLET_ANIM_LAYER,
                                  restart = False)

                # Out of ammo, play click.
                self.emitSound("Building_Sentrygun.Empty")

            return True

        def findTarget(self):
            if self.isDisabled():
                return False

            # Loop through players within 1100 units (sentry range).
            sentryOrigin = self.getEyePosition()

            # If we have an enemy get his minimum distance to check against.
            segment = Vec3()
            targetCenter = Vec3()
            minDist2 = 1100 * 1100
            currentTarget = None
            oldTarget = self.enemy
            oldTargetDist2 = 1e+9

            opposingTeam = int(not self.team)

            # Try to attack players first, then objects.
            for player in base.game.playersByTeam[opposingTeam]:
                if player.isDead():
                    continue

                targetCenter = player.getPos()
                targetCenter += player.viewOffset
                segment = targetCenter - sentryOrigin
                dist2 = segment.lengthSquared()

                # Store the current target distance if we come across it.
                if player == oldTarget:
                    oldTargetDist2 = dist2

                # Check to see if the target is closer than the already validated target.
                if dist2 > minDist2:
                    continue

                # It is closer, check to see if the target is valid.
                if self.isValidTargetPlayer(player, sentryOrigin, targetCenter):
                    minDist2 = dist2
                    currentTarget = player

            # If we already have a target, don't check objects.
            if currentTarget is None:
                for obj in base.game.objectsByTeam[opposingTeam]:
                    targetCenter = obj.getEyePosition()
                    segment = targetCenter - sentryOrigin
                    dist2 = segment.lengthSquared()

                    # Store the current target distance if we come across it.
                    if obj == oldTarget:
                        oldTargetDist2 = dist2

                    # Check to see if the target is closer than the already validated target.
                    if dist2 > minDist2:
                        continue

                    # It is closer, check to see if the target is valid.
                    if self.isValidTargetObject(obj, sentryOrigin, targetCenter):
                        minDist2 = dist2
                        currentTarget = obj

            # We have a target.
            if currentTarget:
                if currentTarget != oldTarget:
                    # minDist2 is the new target's distance
                    # oldTargetDist2 is the old target's distance
                    # Don't switch unless the new target is closer by some
                    # percentage.
                    if minDist2 < (oldTargetDist2 * 0.75):
                        self.foundTarget(currentTarget, sentryOrigin)
                return True

            return False

        def sentryRotate(self):
            # Stop the bullet firing animation channel.
            self.stop(layer = SENTRYGUN_BULLET_ANIM_LAYER, kill = False)

            # Animate
            self.character.update()

            # Look for a target
            if self.findTarget():
                return

            # Rotate
            if not self.moveTurret():
                # Change direction

                if self.isDisabled():
                    self.emitSound("Building_Sentrygun.Disabled")
                    self.goalAngles.y = 30
                else:
                    if self.level == 1:
                        self.emitSound("Building_Sentrygun.Idle")
                    elif self.level == 2:
                        self.emitSound("Building_Sentrygun.Idle2")
                    elif self.level == 3:
                        self.emitSound("Building_Sentrygun.Idle3")

                    # Switch rotation direction
                    if self.turningRight:
                        self.turningRight = False
                        self.goalAngles.x = self.leftBound
                    else:
                        self.turningRight = True
                        self.goalAngles.x = self.rightBound

                    # Randomly look up and down a bit
                    if random.uniform(0, 1) < 0.3:
                        self.goalAngles.y = -random.randint(-10, 10)
    else:
        def delete(self):
            self.ivYaw = None
            self.ivPitch = None
            BaseObject.delete(self)

        def onModelChanged(self):
            BaseObject.onModelChanged(self)
            # Make sure pose parameters carry over to new model.
            self.setLookPitch(self.ivPitch.getInterpolatedValue())
            self.setLookYaw(self.ivYaw.getInterpolatedValue())

        def announceGenerate(self):
            BaseObject.announceGenerate(self)
            self.findAllMatches("**/*light*").hide()
            #self.findAllMatches("**/*")

        def RecvProxy_objectState(self, state):
            if state == ObjectState.Constructing:
                self.findAllMatches("**/*toolbox*").show()
            else:
                self.findAllMatches("**/*toolbox*").hide()
            self.objectState = state

        def RecvProxy_lookPitch(self, pitch):
            self.setLookPitch(pitch)

        def RecvProxy_lookYaw(self, yaw):
            self.setLookYaw(yaw)

        def getLookPitch(self):
            return self.lookPitch

        def setLookPitch(self, pitch):
            self.lookPitch = pitch
            self.getPoseParameter("aim_pitch").setNormValue(pitch)

        def getLookYaw(self):
            return self.lookYaw

        def setLookYaw(self, yaw):
            self.lookYaw = yaw
            self.getPoseParameter("aim_yaw").setNormValue(yaw)

if not IS_CLIENT:
    SentryGunAI = SentryGun
    SentryGunAI.__name__ = 'SentryGunAI'

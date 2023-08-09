
import random

from panda3d.core import *

from tf.player.DistributedTFPlayerAI import DistributedTFPlayerAI
from tf.player.InputButtons import InputFlag
from tf.player.PlayerCommand import PlayerCommand
from tf.player.TFClass import BaseSpeed, Class
from tf.tfbase import CollisionGroups, TFFilters, TFGlobals


class TacicalMode:
    Retreat = 0
    Ambush = 1
    Strafe = 2
    COUNT = 3

class ConfidenceLevel:
    Low = 0
    Medium = 1
    High = 2
    COUNT = 3

class SkillLevel:
    Low = 0
    Medium = 1
    High = 2
    COUNT = 3

PRIMARY = 0
SECONDARY = 1
MELEE = 2

WeaponDists = {
    Class.Scout: (
        ((0, 200), PRIMARY),
        ((250, 1000000), SECONDARY),
        ((0, 64), MELEE)
    ),

    Class.Soldier: (
        ((200, 1000000), PRIMARY),
        ((0, 300), SECONDARY),
        ((0, 64), MELEE)
    ),

    Class.Pyro: (
        ((0, 300), PRIMARY),
        ((0, 1000000), SECONDARY),
        ((0, 64), MELEE)
    ),

    Class.Demo: (
        ((200, 100000), PRIMARY),
        ((0, 200), MELEE)
    ),

    Class.HWGuy: (
        ((0, 100000), PRIMARY),
        ((0, 100000), SECONDARY),
        ((0, 64), MELEE)
    ),

    Class.Engineer: (
        ((0, 250), PRIMARY),
        ((300, 1000000), SECONDARY),
        ((0, 64), MELEE)
    ),

    Class.Medic: (
        ((0, 64), SECONDARY),
    ),

    Class.Sniper: (
        ((700, 100000), PRIMARY),
        ((64, 800), SECONDARY),
        ((0, 64), MELEE)
    ),

    Class.Spy: (
        ((64, 100000), PRIMARY),
        ((0, 64), SECONDARY)
    )
}

class EnemySelection:

    """
    get all visible players
    sort players by damage dealt to me
    if has it, pick closest player that has dealt most damage
    if no damage, sort by distance
    pick closest player looking towards me
    """

    def __init__(self, bot):
        self.bot = bot
        self.visiblePlayers = []
        self.playerDamages = {}

    def addPlayerDamage(self, player, dmg):
        if not player in self.playerDamages:
            self.playerDamages[player] = [dmg, globalClock.frame_time]
        else:
            self.playerDamages[player][0] += dmg
            self.playerDamages[player][1] = globalClock.frame_time

    def clearPlayerDamage(self, plyr):
        if plyr in self.playerDamages:
            del self.playerDamages[plyr]

    def findVisiblePlayers(self):
        viewForward = self.bot.viewAngleQuat.getForward()

        self.visiblePlayers = []

        myEyes = self.bot.getEyePosition()
        for team, players in base.game.playersByTeam.items():
            if team == self.bot.team:
                continue
            for pl in players:
                if pl == self.bot:
                    continue
                if pl.isDead():
                    continue
                toPlayer = (pl.getEyePosition() - myEyes).normalized()
                if toPlayer.dot(viewForward) < 0.35:
                    continue
                if not self.bot.isEntityVisible(pl, CollisionGroups.World)[0]:
                    continue
                self.visiblePlayers.append(pl)

        if self.visiblePlayers:
            self.visiblePlayers.sort(key = lambda x: (x.getEyePosition() - myEyes).lengthSquared())

    def getAggressionRating(self, player):
        # A player is aggressing me if they've done damage to me recently
        # and are looking torwards me.

        if player.team == self.bot.team:
            return 0

        dmgTimeMax = 5.0

        now = globalClock.frame_time

        points = 0

        toMe = (self.bot.getEyePosition() - player.getEyePosition())
        toMeLen = toMe.length()
        toMeDir = toMe.normalized()

        plViewQuat = Quat()
        plViewQuat.setHpr(player.viewAngles)
        plViewFwd = plViewQuat.getForward()

        # Points based on proximity.
        points += TFGlobals.simpleSplineRemapValClamped(toMeLen, 0, 3000, 200, 0)

        # If they're looking at me, add more points.
        dot = toMeDir.dot(plViewFwd)
        if dot > 0:
            points += TFGlobals.simpleSplineRemapValClamped(dot, 0, 1, 0, 100)

        if player.tfClass == Class.HWGuy:
            points += 150
        elif player.tfClass == Class.Soldier:
            points += 100
        elif player.tfClass == Class.Demo:
            points += 75
        elif player.tfClass == Class.Medic:
            points += 150
        elif player.tfClass == Class.Pyro:
            points += 40

        dmgInfo = self.playerDamages.get(player, [0, 0])
        if dmgInfo[0] > 0:
            dmgElapsed = now - dmgInfo[1]
            # 100 baseline points if they've done any damage to me.
            points += 100
            # More points for more damage, but decay it over time.
            points += dmgInfo[0] * (1.0 - max(0.0, min(1.0, dmgElapsed / dmgTimeMax)))

        return points

    def getBestEnemy(self):
        if not self.visiblePlayers:
            return None

        enemies = [x for x in self.visiblePlayers if x.team != self.bot.team]
        aggressors = list(sorted(enemies, key=lambda x: self.getAggressionRating(x), reverse=True))
        if aggressors:
            return aggressors[0]
        else:
            return None

class DistributedTFPlayerBotAI(DistributedTFPlayerAI):

    def __init__(self):
        DistributedTFPlayerAI.__init__(self)
        self.__botCmdNum = 0
        self.currMoveDir = Vec3()
        self.interpMoveDir = Vec3()

        self.enemySelection = EnemySelection(self)

        self.targetPlayer = None

        self.viewAngleQuat = Quat()

        self.weaponObjs = []

        self.tookDamage = False
        self.damagePos = Vec3()
        self.tookDamageTime = 0.0

        self.skillLevel = random.randint(0, SkillLevel.COUNT-1)
        self.tacticalMode = TacicalMode.Strafe
        self.confidenceLevel = random.randint(0, ConfidenceLevel.COUNT-1)
        self.nextTacticalModeChange = 0
        self.nextStrafeChangeTime = 0
        self.lookAroundHpr = Vec3()
        self.nextLookAroundHprChangeTime = 0
        self.strafeDir = 0

        self.combatStanding = 0
        self.targetMovePos = None

        self.accept('PlayerDied', self.__onPlayerDied)

    def selectTacticalMode(self):
        if self.shouldRetreat():
            self.tacticalMode = TacicalMode.Retreat

        elif self.nextTacticalModeChange <= globalClock.frame_time:
            if self.combatStanding >= 400:
                self.tacticalMode = TacicalMode.Ambush
            elif self.combatStanding >= 200:
                self.tacticalMode = TacicalMode.Strafe
            else:
                if self.confidenceLevel == ConfidenceLevel.High:
                    ambushChance = 0.3
                elif self.confidenceLevel == ConfidenceLevel.Medium:
                    ambushChance = 0.1
                elif self.confidenceLevel == ConfidenceLevel.Low:
                    ambushChance = 0.01
                if random.random() <= ambushChance:
                    self.tacticalMode = TacicalMode.Ambush
                else:
                    self.tacticalMode = TacicalMode.Strafe

            self.nextTacticalModeChange = globalClock.frame_time + random.uniform(2, 5)

            if self.tacticalMode == TacicalMode.Strafe:
                self.nextStrafeChangeTime = globalClock.frame_time

    def getMyCombatStanding(self):
        points = self.health * 0.5
        for wpn in self.weaponObjs:
            if wpn.usesClip and wpn.clip > 0:
                points += (wpn.clip / wpn.maxClip) * 50
            elif wpn.usesAmmo and wpn.ammo > 0:
                points += (wpn.clip / wpn.maxAmmo) * 50
        if self.confidenceLevel == ConfidenceLevel.High:
            points *= 2
        elif self.confidenceLevel == ConfidenceLevel.Low:
            points *= 0.5
        return points

    def shouldRetreat(self):
        if not self.targetPlayer:
            return False
        return self.combatStanding <= 100

    def getRetreatTarget(self):
        # Move away from our target enemy.
        if not self.targetPlayer:
            return None

        targetToMe = (self.getPos() - self.targetPlayer.getPos()).normalized()

        # Apply some variance.
        targetToMe.x += random.uniform(-0.3, 0.3)
        targetToMe.y += random.uniform(-0.3, 0.3)
        targetToMe.z = 0
        targetToMe.normalize()

        return self.getPos() + targetToMe * random.uniform(64, 128)

    def getAmbushTarget(self):
        if not self.targetPlayer:
            return None

        targetToMe = (self.getPos() - self.targetPlayer.getPos()).normalized()

        # Go in a half circle around the player randomly.
        targetToMe.x += random.uniform(-0.5, 0.5)
        targetToMe.y += random.uniform(-0.5, 0.5)
        targetToMe.z = 0
        targetToMe.normalize()

        return self.targetPlayer.getPos() + targetToMe * random.uniform(64, 128)

    def getStrafeTargetDir(self):
        if not self.targetPlayer:
            return None

        if self.nextStrafeChangeTime <= globalClock.frame_time:
            self.strafeDir = not self.strafeDir
            self.nextStrafeChangeTime = globalClock.frame_time + random.uniform(0.3, 1.0)

        targetToMe = (self.getPos() - self.targetPlayer.getPos()).normalized()
        meToTarget = -targetToMe

        perp = meToTarget.cross(Vec3.up() if self.strafeDir else Vec3.down())
        perp.x += random.uniform(-0.3, 0.3)
        perp.y += random.uniform(-0.3, 0.3)
        perp.z = 0
        return perp.normalized()

    def __onPlayerDied(self, plyr):
        if plyr == self:
            # Forget the damages that everyone has done to me.
            self.enemySelection.playerDamages = {}
        else:
            # They died, forget their damage.
            self.enemySelection.clearPlayerDamage(plyr)

    def delete(self):
        base.game.botRemoved(self)
        DistributedTFPlayerAI.delete(self)

    def giveClassWeapons(self):
        DistributedTFPlayerAI.giveClassWeapons(self)
        self.weaponObjs = [base.air.doId2do[x] for x in self.weapons]

    def getBestWeaponForTargetDist(self, dist):
        currWpn = self.activeWeapon
        wpn = self.activeWeapon

        clsInfo = WeaponDists.get(self.tfClass)
        if not clsInfo:
            return wpn

        goodWeapons = []

        for dists, slot in clsInfo:
            if dist < dists[0] or dist > dists[1]:
                continue
            wpnObj = self.weaponObjs[slot]
            if not wpnObj:
                continue
            if wpnObj.usesAmmo and wpnObj.ammo <= 0:
                continue
            goodWeapons.append((slot, wpnObj))

        if goodWeapons:
            if len(goodWeapons) > 1:
                # Multiple weapons are valid.  If we are already using one of them,
                # prefer that one, unless the clip ran out.

                withClip = [x for x in goodWeapons if not x[1].usesClip or x[1].clip > 0]
                if withClip:
                    currIsGood = False
                    for slot, _ in withClip:
                        if slot == currWpn:
                            wpn = slot
                            currIsGood = True
                            break
                    if not currIsGood:
                        for slot, _ in withClip:
                            if slot != currWpn:
                                wpn = slot
                                break
                else:
                    currIsGood = False
                    for slot, _ in goodWeapons:
                        if slot == currWpn:
                            wpn = slot
                            currIsGood = True
                            break
                    if not currIsGood:
                        for slot, _ in goodWeapons:
                            if slot != currWpn:
                                wpn = slot
                                break
            else:
                wpn = goodWeapons[0][0]

        return wpn

    def canAttackPlayer(self, pl):
        toPl = (pl.getEyePosition() - self.getEyePosition()).normalized()
        return toPl.dot(self.viewAngleQuat.getForward()) >= 0.7

    def getNewMoveDir(self):
        self.currMoveDir = Vec3(
                random.uniform(-1, 1),
                random.uniform(-1, 1),
                0.0
            ).normalized()

    def determineMoveDir(self):
        #if self.currMoveDir.lengthSquared() == 0:
        #    self.getNewMoveDir()
        #    return

        if self.targetMovePos is None:
            self.currMoveDir = Vec3(0)
            return

        currToTarget = (self.targetMovePos - self.getPos())
        if currToTarget.lengthSquared() < 1:
            self.currMoveDir = Vec3(0)
        else:
            self.currMoveDir = currToTarget.normalized()

    def getLookAroundHpr(self):
        if self.nextLookAroundHprChangeTime <= globalClock.frame_time:
            self.lookAroundHpr = Vec3(
                random.uniform(0, 360),
                random.uniform(-45, 45),
                0
            )
            self.nextLookAroundHprChangeTime = globalClock.frame_time + random.uniform(0.5, 3)
        return self.lookAroundHpr

    def interpView(self):
        q = Quat()

        if self.targetPlayer:
            toPlayer = self.targetPlayer.getWorldSpaceCenter() - self.getEyePosition()
            toPlayer.normalize()
            lookAt(q, toPlayer)
        elif self.tookDamage:
            toDmg = self.damagePos - self.getEyePosition()
            toDmg.normalize()
            lookAt(q, toDmg)
        elif self.currMoveDir.lengthSquared() > 0.001:
            lookAt(q, self.currMoveDir)
        else:
            q.setHpr(self.getLookAroundHpr())

        goalAngles = q.getHpr()

        self.viewAngles[0] = TFGlobals.approachAngle(goalAngles[0], self.viewAngles[0], 270 * globalClock.dt)
        self.viewAngles[1] = TFGlobals.approachAngle(goalAngles[1], self.viewAngles[1], 270 * globalClock.dt)
        self.viewAngles[2] = 0.0
        self.viewAngleQuat.setHpr(self.viewAngles)

    def getWishMove(self):
        #self.interpMoveDir[0] = TFGlobals.approach(self.currMoveDir[0], self.interpMoveDir[0], 1.0 * globalClock.dt)
        #self.interpMoveDir[1] = TFGlobals.approach(self.currMoveDir[0], self.interpMoveDir[1], 1.0 * globalClock.dt)
        #self.interpMoveDir[2] = TFGlobals.approach(self.currMoveDir[2], self.interpMoveDir[2], 1.0 * globalClock.dt)

        if self.currMoveDir.lengthSquared() <= 0.001:
            return Vec3(0, 0, 0)

        normDir = self.currMoveDir.normalized()

        fwdMove = self.viewAngleQuat.getForward().dot(normDir)
        sideMove = self.viewAngleQuat.getRight().dot(normDir)

        move = Vec3(sideMove, fwdMove, 0)
        move.normalize()

        if move[1] < 0:
            move[1] *= BaseSpeed * self.classInfo.BackwardFactor
        else:
            move[1] *= BaseSpeed * self.classInfo.ForwardFactor
        move[0] *= BaseSpeed * self.classInfo.ForwardFactor

        return move

    def onTakeDamage_alive(self, info):
        DistributedTFPlayerAI.onTakeDamage_alive(self, info)

        if self.isDead():
            return

        if info.attacker == self or info.inflictor == self:
            return

        target = None
        if info.attacker and info.attacker.isObject():
            target = info.attacker
        elif info.inflictor and info.inflictor.isObject():
            target = info.inflictor
        elif info.attacker and info.attacker.isPlayer():
            target = info.attacker
        elif info.inflictor and info.inflictor.isPlayer():
            target = info.inflictor

        if not target:
            return

        self.damagePos = Vec3(target.getWorldSpaceCenter())
        self.tookDamage = True
        self.tookDamageTime = globalClock.frame_time

        self.enemySelection.addPlayerDamage(target, abs(info.damage))

    def simulate(self):
        self.bulletForce = Vec3()

        # Make sure to not simulate this guy twice per frame.
        if self.simulationTick == base.tickCount:
            return

        self.simulationTick = base.tickCount

        if self.isDead():
            return

        now = globalClock.frame_time

        if self.tookDamage and (now - self.tookDamageTime) > 3.0:
            self.tookDamage = False

        self.enemySelection.findVisiblePlayers()
        self.targetPlayer = self.enemySelection.getBestEnemy()

        if self.targetPlayer:
            self.combatStanding = self.getMyCombatStanding()
            self.selectTacticalMode()
            if self.tacticalMode == TacicalMode.Retreat:
                self.targetMovePos = self.getRetreatTarget()
            elif self.tacticalMode == TacicalMode.Ambush:
                self.targetMovePos = self.getAmbushTarget()
            else:
                strafeDir = self.getStrafeTargetDir()
                self.targetMovePos = self.getPos() + strafeDir * random.uniform(32, 128)
        else:
            self.targetMovePos = None

        self.determineMoveDir()
        self.interpView()
        move = self.getWishMove()

        #inVel = self.velocity.length()

        self.tickBase = base.tickCount
        dummyCmd = PlayerCommand()
        dummyCmd.tickCount = base.tickCount
        dummyCmd.commandNumber = self.__botCmdNum
        dummyCmd.move = move
        dummyCmd.viewAngles = self.viewAngles
        if self.targetPlayer and self.canAttackPlayer(self.targetPlayer):
            bestWpn = self.getBestWeaponForTargetDist((self.targetPlayer.getEyePosition() - self.getEyePosition()).length())
            dummyCmd.buttons |= InputFlag.Attack1
            if bestWpn != self.activeWeapon:
                dummyCmd.weaponSelect = bestWpn
        self.__botCmdNum += 1
        self.runPlayerCommand(dummyCmd, globalClock.dt)

        #if self.velocity.length() <= inVel * 0.3:
        #    self.getNewMoveDir()

        self.viewAngleQuat.setHpr(self.viewAngles)

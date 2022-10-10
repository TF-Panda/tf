
from direct.distributed2.DistributedObjectAI import DistributedObjectAI
from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.player.DistributedTFPlayerAI import DistributedTFPlayerAI
from tf.player.DViewModelAI import DViewModelAI

from tf.tfbase import TFGlobals, Sounds
from tf.weapon.TakeDamageInfo import TakeDamageInfo, calculateExplosiveDamageForce, clearMultiDamage, applyMultiDamage
from tf.tfbase.TFGlobals import Contents, DamageType, TakeDamage, CollisionGroup, GameZone, TFTeam
from tf.player.TFClass import *
from .DTestCharAI import DTestCharAI
from tf.object.BaseObject import BaseObject

import random
import copy

from panda3d.core import *
from panda3d.pphysics import PhysRayCastResult, PhysQueryNodeFilter

from .DistributedGameBase import DistributedGameBase
from .GameMode import *
from .GameModeCTF import GameModeCTF
from .GameModeTraining import GameModeTraining
from .RoundState import *

class DistributedGameAI(DistributedObjectAI, DistributedGameBase):
    notify = directNotify.newCategory("DistributedGameAI")
    notify.setDebug(True)

    def __init__(self):
        DistributedObjectAI.__init__(self)
        DistributedGameBase.__init__(self)

        self.gameModeImpl = None

        self.waitingForPlayers = True

        self.roundNumber = 0
        self.roundTime = 320
        self.roundTimeRemaining = 0
        self.roundState = RoundState.Setup

        # Number of rounds won by each team.
        self.teamScores = {
            TFTeam.Red : 0,
            TFTeam.Blue : 0,
        }
        # First team to this number of rounds won wins the game.
        self.winningScore = 3

        self.numBlue = 0
        self.numRed = 1
        self.numSoldier = 0
        self.numEngineer = 1
        self.numDemo = 0

        self.playersByTeam = {0: [], 1: []}
        self.objectsByTeam = {0: [], 1: []}

    def inSetup(self):
        return self.roundState == RoundState.Setup

    def playerFallDamage(self, player):
        if player.fallVelocity > 650:
            # Old TFC damage formula.
            fallDamage = 5 * (player.fallVelocity / 300)

            # Fall damage needs to scale according to the player's max health, or
            # it's always going to be much more dangerous to weaker classes than
            # larger.
            ratio = player.maxHealth / 100
            fallDamage *= ratio

            fallDamage *= random.uniform(0.8, 1.2)

            return fallDamage

        return 0.0

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        self.addTask(self.__gameUpdate, "gameUpdate", appendTask=True)

    def newRound(self):
        """
        Starts a new round of the game.  Resets all players to spawn locations,
        resets health, round timer, etc.
        """

        self.roundTimeRemaining = self.gameModeImpl.setupTime + 0.1
        self.roundNumber += 1
        self.roundState = RoundState.Setup
        self.gameModeImpl.onNewRound()

        for players in self.playersByTeam.values():
            for plyr in players:
                plyr.destroyAllObjects()
                plyr.respawn()

        self.notify.info("New round %i" % self.roundNumber)

    def beginRound(self):
        self.notify.info("Begin round %i" % self.roundNumber)
        self.roundState = RoundState.Playing
        self.roundTimeRemaining = self.roundTime
        base.world.emitSound("Ambient.Siren")

        self.gameModeImpl.onBeginRound()

    def endRound(self, winTeam=None):
        self.notify.info("End round %i" % self.roundNumber)
        self.roundState = RoundState.Ended
        self.roundTimeRemaining = 15

        if winTeam is not None:
            self.teamScores[winTeam] += 1
            for plyr in self.playersByTeam[winTeam]:
                base.world.emitSound("Game.YourTeamWon", client=plyr.owner)
            for plyr in self.playersByTeam[not winTeam]:
                base.world.emitSound("Game.YourTeamLost", client=plyr.owner)
        else:
            base.world.emitSound("Game.Stalemate")

        self.gameModeImpl.onEndRound()

    def __gameUpdate(self, task):
        if self.waitingForPlayers:
            self.notify.info("Waiting for players")
            return task.cont

        prevTime = self.roundTimeRemaining
        self.roundTimeRemaining -= globalClock.dt
        time = self.roundTimeRemaining

        if self.roundTimeRemaining <= 0:

            if self.roundState == RoundState.Setup:
                # Setup time over, start the round for real.
                self.beginRound()

            elif self.roundState == RoundState.Playing:
                self.endRound()

            elif self.roundState == RoundState.Ended:
                self.newRound()

        elif self.roundState in [RoundState.Setup, RoundState.Playing]:
            if prevTime > 1 and time <= 1:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins1Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds1seconds")

            elif prevTime > 2 and time <= 2:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins2Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds2seconds")

            elif prevTime > 3 and time <= 3:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins3Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds3seconds")

            elif prevTime > 4 and time <= 4:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins4Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds4seconds")

            elif prevTime > 5 and time <= 5:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 5 seconds.
                    base.world.emitSound("Announcer.RoundBegins5Seconds")
                else:
                    # Mission ends in 5 seconds.
                    base.world.emitSound("Announcer.RoundEnds5seconds")

            elif prevTime > 10 and time <= 10:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 10 seconds.
                    base.world.emitSound("Announcer.RoundBegins10Seconds")
                else:
                    # Mission ends in 10 seconds.
                    base.world.emitSound("Announcer.RoundEnds10seconds")

            elif prevTime > 30 and time <= 30:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 30 seconds.
                    base.world.emitSound("Announcer.RoundBegins30Seconds")
                else:
                    # Mission ends in 30 seconds.
                    base.world.emitSound("Announcer.RoundEnds30seconds")

            elif prevTime > 60 and time <= 60:
                if self.roundState == RoundState.Setup:
                    # Mission begins in 60 seconds.
                    base.world.emitSound("Announcer.RoundBegins60Seconds")
                else:
                    # Mission ends in 60 seconds.
                    base.world.emitSound("Announcer.RoundEnds60seconds")

            elif prevTime > 300 and time <= 300:
                # Mission ends in 5 minutes.
                base.world.emitSound("Announcer.RoundEnds5minutes")

        return task.cont

    def collectTeamSpawns(self):

        from .EntityRegistry import EntityRegistry

        self.teamSpawns = {0: [], 1: []}

        levelEnts = []

        for i in range(self.lvlData.getNumEntities()):
            ent = self.lvlData.getEntity(i)

            entCls = EntityRegistry.get(ent.getClassName(), None)
            if entCls:
                print("Generating a", ent.getClassName())
                entObj = entCls()
                entObj.initFromLevel(ent, ent.getProperties())
                base.air.generateObject(entObj, GameZone, announce=False)
                levelEnts.append(entObj)
            else:
                if ent.getClassName() != "info_player_teamspawn":
                    continue
                props = ent.getProperties()
                origin = Vec3()
                angles = Vec3()
                props.getAttributeValue("origin").toVec3(origin)
                props.getAttributeValue("angles").toVec3(angles)
                team = props.getAttributeValue("TeamNum").getInt() - 2
                if team >= 0 and team <= 1:
                    self.teamSpawns[team].append((origin, angles))

        for entObj in levelEnts:
            entObj.announceGenerate()
            assert entObj.isDOAlive()

    def changeLevel(self, lvlName):
        DistributedGameBase.changeLevel(self, lvlName)

        self.collectTeamSpawns()

        pfx = lvlName.split('_')[0]
        self.gameMode = MapPrefixToGameMode.get(pfx, GameMode.Training)
        assert pfx is not None
        self.notify.info("Game mode is %s" % pfx)
        if self.gameMode == GameMode.CTF:
            self.gameModeImpl = GameModeCTF(self)
        elif self.gameMode == GameMode.Training:
            self.gameModeImpl = GameModeTraining(self)

        #
        # Free up memory from the darn cube map textures embedded in the level.
        # We ought to implement some way to just create dummy 1x1 textures on
        # the server.
        #

        # This clears the lightmap textures and cube maps assigned to level
        # geometry.
        for tex in self.lvl.findAllTextures():
            #print(tex, tex.getKeepRamImage())
            tex.clearRamImage()

        # Clear all the cube map textures.
        for i in range(self.lvlData.getNumCubeMaps()):
            mcm = self.lvlData.getCubeMap(i)
            tex = mcm.getTexture()
            if tex:
                #print(tex, tex.getKeepRamImage())
                tex.clearRamImage()

        # Clear all material textures, such as albedos and normal maps.
        for mat in self.lvl.findAllMaterials():
            for i in range(mat.getNumParams()):
                param = mat.getParam(i)
                if isinstance(param, MaterialParamTexture):
                    tex = param.getValue()
                    if tex:
                        #print(tex, tex.getKeepRamImage())
                        tex.clearRamImage()

    def d_doExplosion(self, pos, scale):
        self.sendUpdate('doExplosion', [pos, scale])

    def radiusDamage(self, info, origin, radius, ignoreClass, ignoreEntity):
        from tf.entity.DistributedEntity import DistributedEntity

        mask = Contents.Solid | Contents.AnyTeam

        src = Vec3(origin)

        if info.damageType & DamageType.RadiusMax:
            falloff = 0.0
        elif info.damageType & DamageType.HalfFalloff:
            falloff = 0.5
        elif radius:
            falloff = info.damage / radius
        else:
            falloff = 1.0

        inflictor = info.inflictor

        for do in list(base.net.doId2do.values()):
            if not isinstance(do, DistributedEntity):
                continue

            if (src - do.getPos()).length() > radius:
                continue

            # This value is used to scale damage when the explosion is blocked by some other object.
            blockedDamagePercent = 0.0

            if do == ignoreEntity:
                continue

            if do.takeDamageMode == TakeDamage.No:
                continue

            # Check that the explosion can "see" the entity.
            spot = do.getPos() + (do.viewOffset * 0.5)
            res = PhysRayCastResult()
            dir = spot - src
            dist = dir.length()
            dir.normalize()
            filter = PhysQueryNodeFilter(info.inflictor, PhysQueryNodeFilter.FTExclude)
            base.physicsWorld.raycast(res, src, dir, dist, mask, Contents.Empty, CollisionGroup.Projectile, filter)
            if res.hasBlock():
                b = res.getBlock()
                hitEnt = b.getActor().getPythonTag("entity")
                if hitEnt and hitEnt != do:
                    # Explosion blocked by this entity.
                    continue
                endPos = b.getPosition()
            else:
                hitEnt = do
                endPos = spot

            # Adjust the damage - apply falloff.
            adjustedDamage = 0.0
            distToEnt = 0.0

            # Rockets store the ent they hit as the enemy and have already
            # dealt full damage to them by this time.
            if inflictor and (do == inflictor.enemy):
                # Full damage, we hit this entity directly
                distToEnt = 0.0
            elif do.isPlayer():
                # Use whichever is closer, getPos or world space center
                toWorldSpaceCenter = (src - do.getWorldSpaceCenter()).length()
                toOrigin = (src - do.getPos()).length()
                distToEnt = min(toWorldSpaceCenter, toOrigin)
            else:
                distToEnt = (src - endPos).length()

            #print("Dist to ", do, do.__class__.__name__, distToEnt)

            adjustedDamage = TFGlobals.remapValClamped(distToEnt, 0, radius, info.damage, info.damage * falloff)

            # Take a little less damage from yourself
            if hitEnt == info.attacker:
                #print("Adjust for myself")
                adjustedDamage *= 0.75

            #print("Adjusted damage", adjustedDamage)

            if adjustedDamage <= 0:
                continue

            # The explosion can "see" this entity, so hurt them!

            adjustedInfo = copy.copy(info)
            adjustedInfo.setDamage(adjustedDamage - (adjustedDamage * blockedDamagePercent))

            #print("Doing", adjustedInfo.damage, "to", do)

            # If we don't have a damage force, manufacture one.
            if adjustedInfo.damagePosition == Vec3() or adjustedInfo.damageForce == Vec3():
                calculateExplosiveDamageForce(adjustedInfo, dir, src, 1.0)
            else:
                # Assume the force passed in is the maximum force, decay based on falloff.
                force = adjustedInfo.damageForce.length() * falloff
                adjustedInfo.damageForce = dir * force
                adjustedInfo.damagePosition = Vec3(src)

            #print("Doing radius damage to", do)

            if res.hasBlock() and do == hitEnt:
                clearMultiDamage()
                do.dispatchTraceAttack(adjustedInfo, dir, res.getBlock())
                applyMultiDamage()
            else:
                do.takeDamage(adjustedInfo)

            # TODO: hit all triggers

    def d_doTracers(self, origin, ends, excludeClients = []):
        self.sendUpdate('doTracers', [origin, ends], excludeClients = excludeClients)

    def playerCanTakeDamage(self, player, inflictor):
        if player == inflictor:
            # We can damage ourselves.
            return True
        elif isinstance(inflictor, BaseObject):
            if player.doId == inflictor.builderDoId or player.team != inflictor.team:
                # Builder and enemies.
                return True
            else:
                # Teammates of the builder.
                return False
        else:
            # Otherwise, only if we are on different teams.
            return player.team != inflictor.team

    def allowDamage(self, player, inflictor):
        return player.getTeam() != inflictor.getTeam()

    def joinGame(self, name):
        print("Player " + name + " has joined the game.")

        client = base.sv.clientSender
        player = DistributedTFPlayerAI()
        client.player = player
        player.playerName = name
        #player.team = 1
        if self.numRed > self.numBlue:
            # Blue team
            player.team = 1
            self.numBlue += 1
        else:
            # Red team
            player.team = 0
            self.numRed += 1
        player.skin = player.team
        if self.numEngineer > self.numSoldier:
            tfclass = Class.Soldier
            self.numSoldier += 1
        else:
            tfclass = Class.Demo
            self.numEngineer += 1
        self.playersByTeam[player.team].append(player)
        player.changeClass(tfclass, force = True, sendRespawn = False, giveWeapons = False)
        # FIXME!!!!!
        base.sv.generateObject(player, TFGlobals.GameZone, client)
        player.giveClassWeapons()

        if self.waitingForPlayers:
            self.waitingForPlayers = False
            self.newRound()

        self.sendUpdate('joinGameResp', [base.tickCount], client=client)


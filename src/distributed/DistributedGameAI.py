
import copy
import random

from panda3d.core import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed2.DistributedObjectAI import DistributedObjectAI
from direct.distributed2.ServerRepository import ServerRepository
from tf.bot.DistributedTFPlayerBotAI import DistributedTFPlayerBotAI
from tf.entity.DistributedEntity import DistributedEntity
from tf.entity.EntityRegistryAI import EntityRegistry
from tf.entity.TFGameRulesProxyAI import TFGameRulesProxyAI
from tf.object.BaseObject import BaseObject
from tf.player.DistributedTFPlayerAI import DistributedTFPlayerAI
from tf.player.TFClass import *
from tf.tfbase import CollisionGroups, TFFilters, TFGlobals, TFLocalizer
from tf.tfbase.TFGlobals import DamageType, GameZone, TakeDamage, TFTeam
from tf.weapon.TakeDamageInfo import (applyMultiDamage,
                                      calculateExplosiveDamageForce,
                                      clearMultiDamage)

from .DistributedGameBase import DistributedGameBase
from .GameMode import *
from .GameModeArena import GameModeArena
from .GameModeCTF import GameModeCTF
from .GameModePayload import GameModePayload
from .GameModeTraining import GameModeTraining
from .RoundState import *

BotNames = ["Bot"]

class DistributedGameAI(DistributedObjectAI, DistributedGameBase):
    notify = directNotify.newCategory("DistributedGameAI")
    notify.setDebug(True)

    def __init__(self):
        DistributedObjectAI.__init__(self)
        DistributedGameBase.__init__(self)

        self.gameModeImpl = None

        self.waitingForPlayers = True

        self.maxPlayersPerTeam = base.sv.getMaxClients() // TFTeam.COUNT

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

        self.playersByTeam = {TFTeam.Red: [], TFTeam.Blue: []}
        self.objectsByTeam = {TFTeam.Red: [], TFTeam.Blue: []}

        self.respawnWaves = {TFGlobals.TFTeam.Red: {'time': 10.0, 'wave': 0, 'nextWave': 0.0},
                             TFGlobals.TFTeam.Blue: {'time': 10.0, 'wave': 0, 'nextWave': 0.0}}

        self.roundEndTime = 0

        self.switchTeamsOnNewRound = False
        self.forceMapReset = False
        self.inOverTime = False
        self.controlPointMaster = None
        self.roundTimer = None
        self.gameRulesProxy = None
        self.logicAutos = []

        self.levelEnts = []

        self.allPlayers = {}

        self.availableBotNames = list(BotNames)
        self.bots = []

    def getRespawnWaveTimeForTeam(self, team):
        waveTime = self.respawnWaves[team]['time']
        numPlayers = len(self.playersByTeam[team])

        if numPlayers >= 8:
            return waveTime
        elif numPlayers <= 3:
            return min(5.0, waveTime)
        elif waveTime > 5.0:
            # Somewhere between 4 and 7 players, lerp
            # the wave time from the configured value down to the
            # minimum 5 seconds.
            frac = (numPlayers - 3) / 5
            return min(5.0, waveTime * frac + 5.0 * (1 - frac))
        else:
            return waveTime

    def getNextRespawnWaveTimeForTeam(self, team):
        """
        Returns the time of the *next* respawn wave after the current one.
        """
        return self.respawnWaves[team]['nextWave'] + self.getRespawnWaveTimeForTeam(team)

    def __respawnWaveUpdate(self):
        for team, data in self.respawnWaves.items():
            if data['nextWave'] <= base.clockMgr.getTime():
                waveIval = self.getRespawnWaveTimeForTeam(team)
                data['nextWave'] = base.clockMgr.getTime() + waveIval

    def setTeamRespawnWaveTime(self, team, time):
        self.respawnWaves[team]['time'] = time

    def setTeamGoalString(self, team, string):
        for p in self.playersByTeam[team]:
            self.sendUpdate('setGoalString', [string, team], client=p.owner)

    def spawnPointFilter(self, point, player):

        pointTeam = point.team

        if self.controlPointMaster:

            # Custom filter logic if we're playing control points.

            if point.controlPoint:
                # The spawn point's team must own the indicated control
                # point for it to be active.
                if point.controlPoint.ownerTeam != pointTeam:
                    return False

            currRound = self.controlPointMaster.currentRound

            if currRound:
                # The spawn point may be assigned to a different team based on
                # the current CP round.

                #print(player.team, point.blueCPRound, point.redCPRound, currRound)

                if point.blueCPRound:
                    if player.team == TFGlobals.TFTeam.Blue:
                        if point.blueCPRound == currRound:
                            return True
                        return False

                if point.redCPRound:
                    if player.team == TFGlobals.TFTeam.Red:
                        if point.redCPRound == currRound:
                            return True
                        return False

        if not point.enabled:
            return False

        return player.team == pointTeam

    def getSpawnPointForPlayer(self, player):
        #print("current round", self.controlPointMaster.currentRound)
        spawnPoints = [x for x in self.teamSpawns if self.spawnPointFilter(x, player)]
        return random.choice(spawnPoints)

    def canFinishRound(self):
        """
        Returns True if the round can finish right now, or False if the round
        be in overtime.
        """

        # If we're playing control points, don't end the round if a control point
        # has progress on a capture.
        if self.controlPointMaster:
            return self.controlPointMaster.areAllPointsIdle()

        return True

    def d_setGameContextMessage(self, id, duration, aboutTeam, forTeam=None, forPlayer=None, exclude=[]):
        if forTeam is not None:
            for plyr in self.playersByTeam[forTeam]:
                if plyr in exclude:
                    continue
                self.sendUpdate('setGameContextMessage', [id, duration, aboutTeam], client=plyr.owner)
        else:
            assert forPlayer is not None
            self.sendUpdate('setGameContextMessage', [id, duration, aboutTeam], client=forPlayer.owner)

    def getTeamName(self, team):
        if team == TFTeam.Red:
            return TFLocalizer.RED
        elif team == TFTeam.Blue:
            return TFLocalizer.BLU
        else:
            return ""

    def d_displayChat(self, text, client=None, excludeClients=[]):
        """
        Chat message sent from the server to communicate game events.

        TODO: Figure out how to localize these.
        """
        self.sendUpdate('displayChat', [text], client=client, excludeClients=excludeClients)

    def computeShakeAmplitude(self, center, playerCenter, amplitude, radius):
        if radius <= 0:
            return amplitude

        localAmplitude = -1
        delta = center - playerCenter
        distance = delta.length()

        if distance <= radius:
            # Make the amplitude fall off over distance
            perc = 1.0 - (distance / radius)
            localAmplitude = amplitude * perc
        return localAmplitude

    def doScreenShake(self, center, amplitude, freq, duration, radius, command, airShake):
        amplitude = min(16.0, amplitude)
        for player in self.allPlayers.values():
            # Only start shakes for players that are on the ground unless doing an air shake.
            if not airShake and not player.onGround:
                continue

            localAmplitude = self.computeShakeAmplitude(center, player.getWorldSpaceCenter(), amplitude, radius)
            # This happens if the player is outside the radius, in which case we should ignore
            # all commands.
            if localAmplitude <= 0:
                continue

            # Send the shake to them.
            player.sendUpdate('screenShake', [command, localAmplitude, freq, duration], client=player.owner)

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

    def getAvailableTeam(self):
        # Returns the team with the fewest number of players.

        teams = [TFTeam.Red, TFTeam.Blue]
        teams.sort(key=lambda x: len(self.playersByTeam[x]))

        team = teams[0]
        assert len(self.playersByTeam[team]) < self.maxPlayersPerTeam

        return team

    def enemySound(self, snd, team):
        for plyr in self.playersByTeam[TFGlobals.getEnemyTeam(team)]:
            base.world.emitSound(snd, client=plyr.owner)

    def teamSound(self, snd, team):
        for plyr in self.playersByTeam[team]:
            base.world.emitSound(snd, client=plyr.owner)

    def getNextTeam(self, team):
        """
        Returns team to switch to on a round end with team switch.
        """
        if team == TFTeam.Red:
            return TFTeam.Blue
        else:
            return TFTeam.Red

    def newRound(self):
        """
        Starts a new round of the game.  Resets all players to spawn locations,
        resets health, round timer, etc.
        """

        self.sendUpdate('hideWinPanel')

        self.roundNumber += 1

        self.winTeam = TFTeam.NoTeam

        if self.forceMapReset:
            self.reloadLevelEntities()

        if self.roundTimer:
            if self.roundTimer.setupLength > 0:
                self.roundTimer.startSetupTimer()
                self.roundState = RoundState.Setup
            else:
                self.roundState = RoundState.Playing
        else:
            self.roundState = RoundState.Playing
        self.gameModeImpl.onNewRound()

        for la in self.logicAutos:
            la.connMgr.fireOutput("OnMultiNewRound")

        messenger.send('OnNewRound')

        # Copy the team list so we can switch teams while iterating.
        teamCopy = {}
        for team, players in self.playersByTeam.items():
            teamCopy[team] = list(players)
        for players in teamCopy.values():
            for plyr in players:
                if self.switchTeamsOnNewRound:
                    otherTeam = self.getNextTeam(plyr.team)
                    plyr.doChangeTeam(otherTeam, removeNemesises=False, announce=False)
                else:
                    plyr.destroyAllObjects()
                    plyr.doRespawn()
                # Speak about the round starting (battle cry)
                plyr.speakConcept(TFGlobals.SpeechConcept.RoundStart, {})

        self.notify.info("New round %i" % self.roundNumber)

        if self.switchTeamsOnNewRound:
            self.d_displayChat("Teams have been switched.")

        self.switchTeamsOnNewRound = False
        self.forceMapReset = False
        self.inOverTime = False

        if self.roundState == RoundState.Playing:
            self.beginRound()

    def beginRound(self):
        self.notify.info("Begin round %i" % self.roundNumber)
        if self.roundState == RoundState.Setup:
            base.world.emitSound("Ambient.Siren")
        self.roundState = RoundState.Playing
        self.winTeam = TFTeam.NoTeam
        self.inOverTime = False

        self.gameModeImpl.onBeginRound()

        messenger.send('OnBeginRound')

    def endRound(self, winTeam=TFTeam.NoTeam, winReason=TFGlobals.WinReason.Stalemate):
        self.notify.info("End round %i" % self.roundNumber)
        self.roundState = RoundState.Ended
        self.roundEndTime = base.clockMgr.getTime() + 15.0
        self.inOverTime = False
        if self.roundTimer:
            # Abort the round timer.
            self.roundTimer.stopTimer()

        if winTeam is None:
            winTeam = TFTeam.NoTeam

        conceptData = {
            'isstalemate': winTeam == TFTeam.NoTeam,
            'winteam': winTeam
        }

        if winTeam != TFTeam.NoTeam:
            self.teamScores[winTeam] += 1
            for plyr in self.playersByTeam[winTeam]:
                plyr.setCondition(plyr.CondWinner)
                plyr.updateClassSpeed()
                plyr.speakConcept(TFGlobals.SpeechConcept.RoundEnd, conceptData)
                base.world.emitSound("Game.YourTeamWon", client=plyr.owner)
            for plyr in self.playersByTeam[TFGlobals.getEnemyTeam(winTeam)]:
                plyr.setCondition(plyr.CondLoser)
                plyr.setActiveWeapon(-1)
                plyr.updateClassSpeed()
                plyr.speakConcept(TFGlobals.SpeechConcept.RoundEnd, conceptData)
                base.world.emitSound("Game.YourTeamLost", client=plyr.owner)
        else:
            for teamPlyrs in self.playersByTeam.values():
                for plyr in teamPlyrs:
                    plyr.setCondition(plyr.CondLoser)
                    plyr.setActiveWeapon(-1)
                    plyr.updateClassSpeed()
                    plyr.speakConcept(TFGlobals.SpeechConcept.RoundEnd, conceptData)
            base.world.emitSound("Game.Stalemate")

        self.winTeam = winTeam

        self.gameModeImpl.onEndRound()

        messenger.send('OnEndRound')

        self.sendUpdate('showWinPanel', [winTeam, winReason])

    def __gameUpdate(self, task):
        if self.waitingForPlayers:
            self.notify.info("Waiting for players")
            return task.cont

        self.__respawnWaveUpdate()

        if base.clockMgr.getTime() >= self.roundEndTime:
            if self.roundState == RoundState.Ended:
                self.newRound()

        return task.cont

    def reloadLevelEntities(self):
        preserveEntClassNames = [
            "worldspawn"
        ]
        if self.gameRulesProxy and (self.gameRulesProxy not in self.levelEnts):
            self.gameRulesProxy.disable()
            self.gameRulesProxy.delete()
            self.gameRulesProxy = None
        for ent in reversed(list(self.levelEnts)):
            if ent.className in preserveEntClassNames:
                continue
            if ent.isNetworkedEntity():
                base.air.deleteObject(ent)
            else:
                ent.disable()
                ent.delete()
            self.levelEnts.remove(ent)

        # Now load them up again, but ignoring the classnames
        # we preserved.
        self.loadLevelEntities(preserveEntClassNames)

    def loadLevelEntities(self, ignoreClassNames=[]):
        for i in range(self.lvlData.getNumEntities()):
            ent = self.lvlData.getEntity(i)

            if ent.getClassName() in ignoreClassNames:
                continue

            entCls = EntityRegistry.get(ent.getClassName(), None)
            if entCls:
                print("Generating a", ent.getClassName())
                entObj = entCls()
                entObj.initFromLevel(ent, ent.getProperties())
                if entObj.isNetworkedEntity():
                    base.air.generateObject(entObj, GameZone, announce=False)
                else:
                    entObj.generate()
                self.levelEnts.append(entObj)

        for entObj in self.levelEnts:
            entObj.announceGenerate()
            if entObj.isNetworkedEntity():
                assert entObj.isDOAlive()

        self.teamSpawns = base.entMgr.findAllEntitiesByClassName("info_player_teamspawn")

        gameRulesProxies = base.entMgr.findAllEntitiesByClassName("tf_gamerules")
        assert len(gameRulesProxies) <= 1
        if gameRulesProxies:
            self.gameRulesProxy = gameRulesProxies[0]
        else:
            self.gameRulesProxy = TFGameRulesProxyAI()

        self.logicAutos = base.entMgr.findAllEntitiesByClassName("logic_auto")
        for la in self.logicAutos:
            la.connMgr.fireOutput("OnMultiNewMap")
            la.connMgr.fireOutput("OnMapSpawn")

    def changeLevel(self, lvlName):
        DistributedGameBase.changeLevel(self, lvlName)

        pfx = Filename.fromOsSpecific(lvlName).getBasenameWoExtension().split('_')[0]
        self.gameMode = MapPrefixToGameMode.get(pfx, GameMode.Training)
        assert pfx is not None
        self.notify.info("Game mode is %s" % pfx)
        if self.gameMode == GameMode.CTF:
            self.gameModeImpl = GameModeCTF(self)
        elif self.gameMode == GameMode.Training:
            self.gameModeImpl = GameModeTraining(self)
        elif self.gameMode == GameMode.Payload:
            self.gameModeImpl = GameModePayload(self)
        elif self.gameMode == GameMode.Arena:
            self.gameModeImpl = GameModeArena(self)

        self.loadLevelEntities()

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

    def d_doExplosion(self, pos, scale, dir):
        #base.air.sendUpdatePHSOnly(self, 'doExplosion', [pos, scale, dir], pos)
        self.sendUpdate('doExplosion', [pos, scale, dir])

    def radiusDamage(self, info, origin, radius, ignoreClass, ignoreEntity):
        # I don't think other players/buildings should block splash damage.
        mask = CollisionGroups.World# | CollisionGroups.Mask_AllTeam

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

        filter = TFFilters.TFQueryFilter(inflictor)

        for do in list(base.net.doId2do.values()):
            if do == info.inflictor:
                continue

            if do.isDODeleted():
                continue

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
            tr = TFFilters.traceLine(src, spot, mask, filter)
            if tr['hit']:
                hitEnt = tr['ent']
                if hitEnt and hitEnt != do:
                    # Explosion blocked by this entity.
                    continue
                endPos = tr['endpos']
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

            adjustedDamage = TFGlobals.remapValClamped(distToEnt, 0, radius, info.damage, info.damage * falloff)

            # Take a little less damage from yourself
            if hitEnt == info.attacker:
                adjustedDamage *= 0.75

            if adjustedDamage <= 0:
                continue

            # The explosion can "see" this entity, so hurt them!

            adjustedInfo = copy.copy(info)
            adjustedInfo.setDamage(adjustedDamage - (adjustedDamage * blockedDamagePercent))

            # If we don't have a damage force, manufacture one.
            if adjustedInfo.damagePosition == Vec3() or adjustedInfo.damageForce == Vec3():
                calculateExplosiveDamageForce(adjustedInfo, tr['tracedir'], src, 1.0)
            else:
                # Assume the force passed in is the maximum force, decay based on falloff.
                force = adjustedInfo.damageForce.length() * falloff
                adjustedInfo.damageForce = tr['tracedir'] * force
                adjustedInfo.damagePosition = Vec3(src)

            if tr['hit'] and do == hitEnt:
                clearMultiDamage()
                do.dispatchTraceAttack(adjustedInfo, tr['tracedir'], tr)
                applyMultiDamage()
            else:
                do.takeDamage(adjustedInfo)

            # TODO: hit all triggers

    def d_doTracers(self, origin, ends, excludeClients = []):
        #base.air.sendUpdatePHSOnly(self, 'doTracers', [origin, ends], origin)
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

        # TODO: Localize server chat messages.
        self.d_displayChat("%s has joined the game." % name)

        client = base.sv.clientSender
        player = DistributedTFPlayerAI()
        client.player = player
        player.playerName = name
        # Automatically assign to team with fewest players.
        team = self.getAvailableTeam()
        # This should be made somewhat cleaner.
        # Changing class cannot force a respawn because we might join in the middle
        # of a round end.
        # We also can't give class weapons until we actually respawn because the
        # player is not yet assigned a doId until we call generateObject().
        player.doChangeTeam(team, respawn=False, giveWeapons=False, isAuto=True)
        #self.d_displayChat("%s was automatically assigned to team %s." % (name, self.getTeamName(team)))
        player.doChangeClass(random.randint(0, Class.COUNT - 1), respawn=False, force=True,
                             sendRespawn=False, giveWeapons=False)
        base.air.generateObject(player, TFGlobals.GameZone, client)
        player.startWaitingToRespawn()

        if self.waitingForPlayers:
            self.waitingForPlayers = False
            self.newRound()

        self.sendUpdate('joinGameResp', [base.tickCount], client=client)

        # Give them magic word access.
        # TODO: Determine who should have access.
        base.air.addExplicitInterest(client, [TFGlobals.MagicWordZone])

    def botRemoved(self, bot):
        if bot in self.bots:
            self.bots.remove(bot)
        #if bot.playerName not in self.availableBotNames:
        #    self.availableBotNames.append(bot.playerName)

    def makeBot(self, _):
        #botName = random.choice(self.availableBotNames)
        #self.availableBotNames.remove(botName)

        botName = "Bot %i" % (len(self.bots) + 1)

        print("Bot " + botName + " has joined the game.")

        dummyClient = ServerRepository.Client(0, 0)

        player = DistributedTFPlayerBotAI()
        player.playerName = botName
        dummyClient.player = player
        # Automatically assign to team with fewest players.
        team = self.getAvailableTeam()
        # This should be made somewhat cleaner.
        # Changing class cannot force a respawn because we might join in the middle
        # of a round end.
        # We also can't give class weapons until we actually respawn because the
        # player is not yet assigned a doId until we call generateObject().
        player.doChangeTeam(team, respawn=False, giveWeapons=False, isAuto=True)
        #self.d_displayChat("%s was automatically assigned to team %s." % (name, self.getTeamName(team)))
        player.doChangeClass(random.randint(0, Class.COUNT - 1), respawn=False, force=True,
                             sendRespawn=False, giveWeapons=False)
        base.sv.generateObject(player, TFGlobals.GameZone, dummyClient, dclassName='DistributedTFPlayerAI')
        player.startWaitingToRespawn()

        self.bots.append(player)

    def clearBots(self):
        for b in list(self.bots):
            base.air.deleteObject(b)
        self.bots = []

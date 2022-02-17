
from direct.distributed2.DistributedObjectAI import DistributedObjectAI

from tf.player.DistributedTFPlayerAI import DistributedTFPlayerAI
from tf.player.DViewModelAI import DViewModelAI

from tf.tfbase import TFGlobals, Sounds
from tf.weapon.TakeDamageInfo import TakeDamageInfo, calculateExplosiveDamageForce, clearMultiDamage, applyMultiDamage
from tf.tfbase.TFGlobals import Contents, DamageType, TakeDamage, CollisionGroup, GameZone
from tf.player.TFClass import *
from .DTestCharAI import DTestCharAI
from tf.object.BaseObject import BaseObject

import random
import copy

from panda3d.core import Vec3
from panda3d.pphysics import PhysRayCastResult, PhysQueryNodeFilter

from .DistributedGameBase import DistributedGameBase

class DistributedGameAI(DistributedObjectAI, DistributedGameBase):

    def __init__(self):
        DistributedObjectAI.__init__(self)
        DistributedGameBase.__init__(self)

        self.numBlue = 0
        self.numRed = 0
        self.numSoldier = 0
        self.numEngineer = 1
        self.numDemo = 0

        self.playersByTeam = {0: [], 1: []}
        self.objectsByTeam = {0: [], 1: []}

    def collectTeamSpawns(self):

        from .EntityRegistry import EntityRegistry

        self.teamSpawns = {0: [], 1: []}

        for i in range(self.lvlData.getNumEntities()):
            ent = self.lvlData.getEntity(i)

            entCls = EntityRegistry.get(ent.getClassName(), None)
            if entCls:
                print("Generating a", ent.getClassName())
                entObj = entCls()
                entObj.initFromLevel(ent.getProperties())
                base.air.generateObject(entObj, GameZone)
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

    def changeLevel(self, lvlName):
        DistributedGameBase.changeLevel(self, lvlName)
        self.collectTeamSpawns()

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
            elif isinstance(do, DistributedTFPlayerAI):
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
            tfclass = Class.Engineer
            self.numEngineer += 1
        self.playersByTeam[player.team].append(player)
        player.changeClass(tfclass, force = True, sendRespawn = False, giveWeapons = False)
        # FIXME!!!!!
        base.sv.generateObject(player, TFGlobals.GameZone, client)
        player.giveClassWeapons()


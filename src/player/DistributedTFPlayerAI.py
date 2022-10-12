
from tf.actor.DistributedCharAI import DistributedCharAI
from direct.distributed2.ServerConfig import *
from .DistributedTFPlayerShared import DistributedTFPlayerShared

from direct.directnotify.DirectNotifyGlobal import directNotify

from .PlayerCommand import PlayerCommand
from .InputButtons import InputFlag
from .TFPlayerAnimStateAI import TFPlayerAnimStateAI
from .PlayerAnimEvent import PlayerAnimEvent
from .TFClass import *
from .DViewModelAI import DViewModelAI
from .ObserverMode import ObserverMode
from tf.weapon.TakeDamageInfo import addMultiDamage, TakeDamageInfo

from tf.tfbase import TFGlobals, Sounds, TFFilters
from tf.tfbase.TFGlobals import Contents, CollisionGroup, TakeDamage, DamageType
from tf.object.BaseObject import BaseObject
from tf.object.ObjectType import ObjectType

from panda3d.core import *
from panda3d.pphysics import PhysRayCastResult, PhysQueryNodeFilter

import copy
import random

tf_damage_range = 0.5
tf_damageforcescale_other = 6.0
tf_damageforcescale_self_soldier = 10.0
tf_damagescale_self_soldier = 0.6
damage_force_self_scale = 9.0

tf_boost_drain_time = 15.0

TF_DEATH_ANIMATION_TIME = 2.0
spec_freeze_time = ConfigVariableDouble("spec-freeze-time", 4.0)
spec_freeze_traveltime = ConfigVariableDouble("spec-freeze-travel-time", 0.4)

class CommandContext:
    def __init__(self):
        self.backupCmds = []
        self.newCmds = []
        self.cmds = []
        self.totalCmds = 0
        self.droppedPackets = 0
        self.paused = False

class PlayerCmdInfo:
    def __init__(self):
        self.time = 0.0
        self.numCmds = 0
        self.droppedPackets = 0

class DistributedTFPlayerAI(DistributedCharAI, DistributedTFPlayerShared):
    notify = directNotify.newCategory("DistributedTFPlayerAI")
    notify.setDebug(True)

    MaxCMDBackup = 64

    def __init__(self):
        DistributedCharAI.__init__(self)
        DistributedTFPlayerShared.__init__(self)
        self.animState = TFPlayerAnimStateAI(self)
        self.commandContexts = []
        self.lastMovementTick = -1
        self.simulationTick = 0
        self.paused = False
        self.lastCmd = PlayerCommand()
        self.currentCommand = None
        self.lastRunCommandNumber = 0
        self.viewAngles = Vec3(0, 0, 0)
        self.nextAttack = 0.0
        self.forceJoint = -1
        self.bulletForce = Vec3(0)

        self.healers = []

        self.flag = None

        self.pendingChangeClass = Class.Invalid

        # Also give them a view model
        self.viewModel = DViewModelAI()
        self.viewModel.player = self

        self.lastPainTime = 0.0
        self.lastVoiceCmdTime = 0.0

        self.healFraction = 0.0
        self.lastDamageTime = 0.0

        self.clientSideAnimation = True

    def __conditionThinkAI(self, task):
        for cond, timeLeft in self.conditions.items():
            if timeLeft != -1:
                reduction = globalClock.dt

                # If we're being healed, we reduce bad conditions faster
                if cond in self.BadConditions and self.healers:
                    reduction += len(self.healers) * reduction * 4

                newTimeLeft = max(timeLeft - reduction, 0)

                if newTimeLeft == 0:
                    self.removeCondition(cond)
                else:
                    self.conditions[cond] = newTimeLeft

        # Our health will only decay (from being medic buffed) if we are not being healed
        # by a medic.
        # Dispensers can give us CondHealthBuff, but will not maintain or give us
        # health above 100%.
        decayHealth = True
        if self.CondHealthBuff in self.conditions:
            timeSinceDamage = globalClock.frame_time - self.lastDamageTime
            scale = TFGlobals.remapValClamped(timeSinceDamage, 10, 15, 1.0, 3.0)

            hasFullHealth = self.health >= self.maxHealth

            totalHealAmount = 0.0
            for healer in self.healers:
                if hasFullHealth and healer['dispenser']:
                    continue

                # Being healed by a medigun, don't decay our health.
                decayHealth = False

                if healer['dispenser']:
                    # Dispensers heal at a slower rate, but ignore scale
                    self.healFraction += globalClock.dt * healer['amount']
                else:
                    # Player heals are affected by the last damage time
                    self.healFraction += globalClock.dt * healer['amount'] * scale

                totalHealAmount += healer['amount']

            healthToAdd = int(self.healFraction)
            if healthToAdd > 0:
                self.healFraction -= healthToAdd

                boostMax = self.getMaxBuffedHealth()

                # TODO: CondDisgused

                # Cap it to the max we'll boost a player's health.
                healthToAdd = max(0, min(healthToAdd, boostMax - self.health))

                self.takeHealth(healthToAdd, DamageType.IgnoreMaxHealth)

            if self.CondBurning in self.conditions:
                # Reduce the duration of this burn
                reduction = 2
                self.flameRemoveTime -= reduction * globalClock.dt

        if decayHealth:
            # If we're not buffed, our health drains back to max
            if self.health > self.maxHealth:
                boostMaxAmount = self.getMaxBuffedHealth() - self.maxHealth
                self.healFraction += globalClock.dt * (boostMaxAmount / tf_boost_drain_time)

                healthToDrain = int(self.healFraction)
                if healthToDrain > 0:
                    self.healFraction -= healthToDrain
                    # Manually subtract the health so we don't generate pain sounds
                    self.health -= healthToDrain

        return task.cont

    def setPos(self, *args, **kwargs):
        DistributedCharAI.setPos(self, *args, **kwargs)
        if self.controller:
            # Keep controller in sync.
            self.controller.foot_position = self.getPos()

    def takeHealth(self, hp, bits):
        if bits & DamageType.IgnoreMaxHealth:
            self.health += hp
            result = True
        else:
            healthToAdd = hp
            maxHealth = self.maxHealth

            if healthToAdd > maxHealth - self.health:
                healthToAdd = maxHealth - self.health

            if healthToAdd <= 0:
                result = False
            else:
                result = DistributedCharAI.takeHealth(self, hp, bits)

        return result

    def getNumHealers(self):
        return len(self.healers)

    def findHealer(self, healer):
        for i in range(len(self.healers)):
            if self.healers[i]['player'] == healer:
                return i

        return -1

    def heal(self, healer, amount, dispenserHeal=False):
        assert self.findHealer(healer) == -1

        data = {
            'player': healer,
            'amount': amount,
            'dispenser': dispenserHeal
        }
        self.healers.append(data)

        if not dispenserHeal:
            self.sendUpdate('setCSHealer', [healer.doId])
            healer.sendUpdate('setCSHealTarget', [self.doId])

        self.setCondition(self.CondHealthBuff)

    def stopHealing(self, healer):
        index = self.findHealer(healer)
        assert index != -1

        theHealerData = self.healers[index]
        self.healers.remove(self.healers[index])

        if not theHealerData['dispenser']:
            gotNewCSHealer = False
            for data in self.healers:
                if not data['dispenser']:
                    self.sendUpdate('setCSHealer', [data['player'].doId])
                    data['player'].sendUpdate('setCSHealTarget', [self.doId])
                    gotNewCSHealer = True
                    break
            if not gotNewCSHealer:
                self.sendUpdate('clearCSHealer')
                theHealerData['player'].sendUpdate('clearCSHealer')

    def recalculateInvuln(self, instantRemove):
        pass

    def playerFallingDamage(self):
        fallDamage = base.game.playerFallDamage(self)
        if fallDamage > 0:
            info = TakeDamageInfo()
            info.inflictor = base.world
            info.attacker = base.world
            info.damage = fallDamage
            info.damageType = DamageType.Fall
            self.takeDamage(info)
            self.emitSound("Player.FallDamage", client=self.owner)
            self.emitSoundSpatial("Player.FallDamage", excludeClients=[self.owner])

    def voiceCommand(self, cmd):
        now = globalClock.frame_time
        if self.isDead() or (now - self.lastVoiceCmdTime) < 1.5:
            return

        voiceLineList = self.classInfo.VoiceCommands.get(cmd)
        if not voiceLineList:
            return

        voiceLine = random.choice(voiceLineList)
        self.d_speak(voiceLine, excludeClients=[self.owner])
        self.d_speak(voiceLine, client=self.owner)

        self.lastVoiceCmdTime = now

    def d_setViewAngles(self, hpr):
        """
        Allows server to override view angles, which are normally
        controlled entirely by the client and sent via player commands.
        """
        self.sendUpdate('setViewAngles', [hpr[0], hpr[1]], client=self.owner)

    def onModelChanged(self):
        DistributedCharAI.onModelChanged(self)
        if self.animState:
            # Re-fetch pose parameters on new model.
            self.animState.onPlayerModelChanged()

    def isPlayer(self):
        """
        Returns True if this entity is a player.  Overridden in
        DistributedTFPlayer to return True.  Convenience method
        to avoid having to check isinstance() or __class__.__name__.
        """
        return True

    def pushExpression(self, name):
        self.sendUpdate('pushExpression', [name])

    def shouldCollide(self, collisionGroup, contentsMask):
        #print("Should collide?", collisionGroup, contentsMask)
        if collisionGroup == CollisionGroup.PlayerMovement or collisionGroup == CollisionGroup.Rockets:
            if self.team == 0:
                if (contentsMask & Contents.RedTeam) == 0:
                    #print("\tno")
                    return False
            elif self.team == 1:
                if (contentsMask & Contents.BlueTeam) == 0:
                    #print("\tno")
                    return False
        #print("\tyes")
        return DistributedCharAI.shouldCollide(self, collisionGroup, contentsMask)

    def d_speak(self, soundName, client = None, excludeClients = []):
        info = Sounds.Sounds.get(soundName, None)
        if not info:
            return
        self.sendUpdate('speak', [info.index], client = client, excludeClients = excludeClients)

    def doClassSpecialSkill(self):
        return

        #if self.tfClass == Class.Engineer:
        #    self.placeSentry()

    def placeSentry(self, rotation):
        if self.selectedBuilding < 0 or self.selectedBuilding > 3:
            return

        metals = [
            130,
            100,
            50,
            50
        ]
        if self.hasObject(self.selectedBuilding) or self.metal < metals[self.selectedBuilding]:
            return

        #if self.sentry:
        #    base.net.deleteObject(self.sentry)
        # Place a sentry in front of him.

        q = Quat()
        q.setHpr(Vec3(self.viewAngles[0], 0, 0))
        fwd = q.getForward()
        startPos = (self.getPos() + (fwd * 64)) + Point3(0, 0, 8)
        # Trace down to get to the floor.
        result = PhysRayCastResult()
        hadHit = base.physicsWorld.raycast(
            result, startPos, Vec3.down(), 1000000,
            Contents.Solid, Contents.Empty, CollisionGroup.Empty,
            TFFilters.TFQueryFilter(
                self, [TFFilters.ignoreSelf])
        )

        good = True
        pos = Point3()
        if hadHit:
            block = result.getBlock()
            actor = block.getActor()
            ent = actor.getPythonTag("entity")
            if not ent or ent.__class__.__name__ != 'WorldAI':
                good = False
            else:
                pos = block.getPosition()
                if (pos - startPos).length() >= 64:
                    good = False
        else:
            good = False

        if not good:
            return False

        if self.selectedBuilding == 0:
            from tf.object.SentryGun import SentryGunAI
            sg = SentryGunAI()
        elif self.selectedBuilding == 1:
            from tf.object.DistributedDispenser import DistributedDispenserAI
            sg = DistributedDispenserAI()
        elif self.selectedBuilding == 2:
            from tf.object.DistributedTeleporter import DistributedTeleporterEntranceAI
            sg = DistributedTeleporterEntranceAI()
        elif self.selectedBuilding == 3:
            from tf.object.DistributedTeleporter import DistributedTeleporterExitAI
            sg = DistributedTeleporterExitAI()

        sg.setBuilderDoId(self.doId)
        sg.setH(rotation)
        sg.setPos(pos)

        self.metal -= metals[self.selectedBuilding]

        base.net.generateObject(sg, self.zoneId)
        #self.sentry = sg

        if self.selectedBuilding == 0:
            self.d_speak(
                random.choice(
                    ["Engineer.AutoBuildingSentry01",
                     "Engineer.AutoBuildingSentry02"]
                )
            )
        elif self.selectedBuilding == 1:
            self.d_speak(
                random.choice(
                    ["Engineer.AutoBuildingDispenser01",
                     "Engineer.AutoBuildingDispenser02"]
                )
            )
        else:
            self.d_speak(
                random.choice(
                    ["Engineer.AutoBuildingTeleporter01",
                     "Engineer.AutoBuildingTeleporter02"]
                )
            )

        return True

    def speakTeleported(self):
        chance = random.random()
        if chance < 0.3:
            self.d_speak(random.choice(self.classInfo.TeleporterThanks))

    def speakHealed(self):
        if self.health >= self.maxHealth:
            chance = random.random()
            if chance < 0.5:
                self.d_speak(random.choice(self.classInfo.ThanksForHeal))

    def getClassSize(self):
        mins = TFGlobals.VEC_HULL_MIN
        maxs = TFGlobals.VEC_HULL_MAX
        return Vec3(maxs[0] - mins[0], maxs[1] - mins[1], maxs[2] - mins[2])

    def onTakeDamage_alive(self, info):
        vecDir = Vec3(0)
        if info.inflictor:
            vecDir = info.inflictor.getWorldSpaceCenter() - Vec3(0, 0, 10) - self.getWorldSpaceCenter()
            vecDir.normalize()

        self.lastDamageTime = globalClock.frame_time

        if info.attacker == self:
            # We damaged ourselves.
            if self.tfClass == Class.Soldier:
                force = vecDir * -self.damageForce(self.getClassSize(), info.damage, tf_damageforcescale_self_soldier)
            else:
                force = vecDir * -self.damageForce(self.getClassSize(), info.damage, damage_force_self_scale)
        elif info.inflictor == base.world:
            force = Vec3(0.0)
        else:
            if info.inflictor.isObject():
                # Sentries push a lot harder
                force = vecDir * -self.damageForce(self.getClassSize(), info.damage, 16)
            else:
                force = vecDir * -self.damageForce(self.getClassSize(), info.damage, tf_damageforcescale_other)
                if self.tfClass == Class.HWGuy:
                    # Heavies take less push from non sentry guns.
                    force *= 0.5

        #print("subtracting", int(info.damage + 0.5), "from tf player hp")
        self.health -= int(info.damage + 0.5)
        if self.health <= 0:
            # Died.
            self.die(info)
            self.health = 0
        else:
            # Only add the damage force if we didn't die.  Otherwise the damage force
            # added to the player velocity will double up with the impulse applied to
            # the ragdoll from the damage.
            self.velocity += force

    def damageForce(self, size, damage, scale):
        force = damage * ((48 * 48 * 82.0) / (size[0] * size[1] * size[2])) * scale
        if force > 1000:
            force = 1000
        return force

    def onTakeDamage(self, inputInfo):
        info = inputInfo#copy.deepcopy(inputInfo)

        if not info.damage:
            return

        if self.isDead():
            return

        healthBefore = self.health
        if not base.game.playerCanTakeDamage(self, info.attacker):
            return

        # If this is our own rocket, scale down the damage
        if self.tfClass == Class.Soldier and info.attacker == self:
            damage = info.damage * tf_damagescale_self_soldier
            info.setDamage(damage)

        # Save damage force for ragdolls.
        self.bulletForce = Vec3(info.damageForce)
        self.bulletForce[0] = max(-15000, min(15000, self.bulletForce[0]))
        self.bulletForce[1] = max(-15000, min(15000, self.bulletForce[1]))
        self.bulletForce[2] = max(-15000, min(15000, self.bulletForce[2]))

        """
        # This is the code for random damage spread from 2007 TF2.
        # Turned off for now, might revisit.

        print("pre-random dmg", info.damage)

        # If we're not damaging ourselves, apply randomness
        if info.attacker != self and not (info.damageType & (DamageType.Drown | DamageType.Fall)):
            damage = 0
            randomDamage = info.damage * tf_damage_range#.getValue()
            minFactor = 0.25
            maxFactor = 0.75
            if info.damageType & DamageType.UseDistanceMod:
                distance = max(1.0, (self.getWorldSpaceCenter() - info.inflictor.getWorldSpaceCenter()).length())
                optimalDistance = 512.0

                center = TFGlobals.remapValClamped(distance / optimalDistance, 0.0, 2.0, 1.0, 0.0)
                if info.damageType & DamageType.NoCloseDistanceMod:
                    if center > 0.5:
                        # Reduce the damage bonus at close rangae
                        center = TFGlobals.remapVal(center, 0.5, 1.0, 0.5, 0.65)
                minFactor = max(0.0, center - 0.25)
                maxFactor = min(1.0, center + 0.25)

            randomVal = random.uniform(minFactor, maxFactor)

            #if (randomVal > 0.5):

            out = TFGlobals.simpleSplineRemapValClamped(randomVal, 0, 1, -randomDamage, randomDamage)
            damage = info.damage + out
            info.damage = damage

        print("post random damage", info.damage)
        """

        self.onTakeDamage_alive(info)

        if self.health > 0:
            # If still alive, flinch
            self.doAnimationEvent(PlayerAnimEvent.Flinch)
            # Flinch the camera up.
            self.punchAngle[1] = 2

            # Look in pain.
            self.pushExpression('pain')

            now = globalClock.frame_time

            if info.damageType & DamageType.Fall:
                self.d_speak(random.choice(self.classInfo.PainFilenames))
                self.lastPainTime = now

            elif (now - self.lastPainTime) >= 0.75:
                # Do sharp pain for local avatar and other players, severe for
                # player that did the damage.
                sharpFname = random.choice(self.classInfo.SharpPainFilenames)
                self.d_speak(sharpFname, excludeClients=[info.attacker.owner])
                severeFname = random.choice(self.classInfo.PainFilenames)
                self.d_speak(severeFname, client=info.attacker.owner)
                self.lastPainTime = now

        #self.bulletForce = Vec3()

    def traceAttack(self, info, dir, hit):
        if self.takeDamageMode != TakeDamage.Yes:
            return

        actor = hit.getActor()
        data = actor.getPythonTag("hitbox")
        if data:
            # Save this joint for the ragdoll.
            self.forceJoint = data[1].joint
        else:
            self.forceJoint = -1

        attacker = info.inflictor
        if attacker:
            # Prevent team damage so blood doesn't appear.
            if not base.game.playerCanTakeDamage(self, attacker):
                return

        addMultiDamage(info, self)

    def doAnimationEvent(self, event, data = 0):
        self.animState.doAnimationEvent(event, data)
        # Broadcast event to clients.
        self.sendUpdate('playerAnimEvent', [event, data])

    def isDead(self):
        return (self.playerState == self.StateDead) or DistributedCharAI.isDead(self)

    def die(self, info = None):
        if self.playerState == self.StateDead:
            return

        if self.flag:
            self.flag.drop()

        if info:
            dmgPos = info.damagePosition
            dmgType = info.damageType
        else:
            dmgPos = Point3()
            dmgType = DamageType.Generic

        if info:
            if info.inflictor and info.inflictor.isObject():
                killer = info.inflictor.doId
            else:
                killer = info.attacker.doId
            base.net.game.sendUpdate('killEvent', [killer, -1, -1, self.doId])
        else:
            # Suicide.
            base.net.game.sendUpdate('killEvent', [self.doId, -1, -1, self.doId])

        # Become a ragdoll.
        #print("Die at forcejoit", self.forceJoint, "force", self.bulletForce + self.velocity)
        if (dmgType & DamageType.Blast) != 0 and self.health <= -20:
            # I think the logic is if the blast damage >= remaining health + 10
            self.sendUpdate('gib', [])
        else:
            self.sendUpdate('becomeRagdoll', [self.forceJoint, dmgPos, self.bulletForce, self.velocity])
        self.disableController()

        # Respawn after 5 seconds.
        self.addTask(self.respawnTask, 'respawn', appendTask = True)

        if info:
            if info.inflictor and info.inflictor.isObject():
                self.observerTarget = info.inflictor.doId
            elif info.inflictor == base.world:
                self.observerTarget = self.doId
            else:
                self.observerTarget = info.attacker.doId
        else:
            self.observerTarget = self.doId

        self.observerMode = ObserverMode.DeathCam
        self.deathTime = globalClock.frame_time
        self.playedFreezeSound = False
        self.abortFreezeCam = False
        self.velocity = Vec3(0)
        self.resetViewPunch()
        self.removeAllConditions()
        if self.activeWeapon != -1:
            wpn = base.net.doId2do.get(self.weapons[self.activeWeapon])
            if wpn:
                wpn.dropAsAmmoPack()
        self.setActiveWeapon(-1)
        self.health = 0

        # Player died.
        if dmgType & DamageType.Fall:
            pain = None
        elif dmgType & DamageType.Club:
            pain = random.choice(self.classInfo.CritPainFilenames)
        elif dmgType & DamageType.Blast:
            pain = random.choice(self.classInfo.SharpPainFilenames)
        elif dmgType & DamageType.Critical:
            pain = random.choice(self.classInfo.CritPainFilenames)
        else:
            pain = random.choice(self.classInfo.PainFilenames)
        if pain:
            self.d_speak(pain)

        self.playerState = self.StateDead

    def respawnTask(self, task):

        now = globalClock.frame_time

        timeInFreeze = spec_freeze_traveltime.getValue() + spec_freeze_time.getValue()
        freezeEnd = (self.deathTime + TF_DEATH_ANIMATION_TIME + timeInFreeze)
        if not self.playedFreezeSound and self.observerTarget != self.doId:
            # Start the sound so that it ends at the freezecam lock on time
            freezeSoundLength = 0.3
            freezeSoundTime = (self.deathTime + TF_DEATH_ANIMATION_TIME) + spec_freeze_traveltime.getValue() - freezeSoundLength
            if now >= freezeSoundTime:
                self.emitSound("TFPlayer.FreezeCam", client=self.owner)
                self.playedFreezeSound = True

        if now >= (self.deathTime + TF_DEATH_ANIMATION_TIME): # allow x seconds death animation/death cam
            if self.observerTarget != self.doId:
                if not self.abortFreezeCam and now < freezeEnd:
                    # Start zooming in on the killer and do the freeze cam.
                    self.observerMode = ObserverMode.FreezeCam
                    return task.cont

        if now < freezeEnd:
            return task.cont

        self.observerTarget = -1
        self.observerMode = ObserverMode.Off

        # Respawn now.

        if self.pendingChangeClass != self.tfClass and self.pendingChangeClass != Class.Invalid:
            self.changeClass(self.pendingChangeClass)
            self.pendingChangeClass = Class.Invalid
        else:
            self.respawn()

        return task.done

    def respawn(self, sendRespawn = True):
        # Refill health
        self.health = self.maxHealth

        # Refill ammo
        for wpnId in self.weapons:
            wpn = base.net.doId2do.get(wpnId)
            wpn.ammo = wpn.maxAmmo
            wpn.clip = wpn.maxClip

        # If we are an Engineer, give 200 metal.  Otherwise only 100 metal.
        # Consistent with original TF2.
        if self.tfClass == Class.Engineer:
            self.metal = 200
        else:
            self.metal = 100

        # Set to the primary weapon
        self.setActiveWeapon(0)

        # Select a random spawn location.
        spawnPoints = base.air.game.teamSpawns[self.team]
        origin, angles = random.choice(spawnPoints)
        # Trace player hull down to find ground.
        tr = TFFilters.traceBox(origin + TFGlobals.VEC_HULL_MIN, origin + TFGlobals.VEC_HULL_MAX,
                                Vec3.down(), 100, TFGlobals.Contents.Solid, 0,
                                TFFilters.TFQueryFilter(self))
        if tr['hit']:
            self.setPos(tr['pos'])
        else:
            self.setPos(origin)
        self.d_setViewAngles((angles[1] - 90, angles[0]))
        # Make client teleport player to respawn location.
        self.teleport()

        if sendRespawn:
            self.sendUpdate('respawn')
        self.playerState = self.StateAlive
        self.enableController()

    def destroyObject(self, index):
        if not self.hasObject(index):
            return
        obj = base.air.doId2do.get(self.objects[index])
        if obj:
            obj.explode()
            base.air.deleteObject(obj)

    def destroyAllObjects(self):
        for objId in self.objects:
            if objId != -1:
                obj = base.air.doId2do.get(objId)
                if obj:
                    obj.explode()
                    base.air.deleteObject(obj)

    def changeClass(self, cls, respawn = True, force = False, sendRespawn = True, giveWeapons = True):
        if (cls == self.tfClass) and not force:
            return

        if (cls < Class.Scout) or (cls > Class.Spy):
            return

        if self.playerState == self.StateAlive:
            self.die()
            self.pendingChangeClass = cls
            return

        # Kill any objects that were built by the player.
        self.destroyAllObjects()

        self.stripWeapons()
        self.tfClass = cls
        self.classInfo = ClassInfos[self.tfClass]
        self.updateClassSpeed()
        self.viewOffset = Vec3(0, 0, self.classInfo.ViewHeight)
        self.maxHealth = self.classInfo.MaxHealth
        self.health = self.maxHealth
        self.loadModel(self.classInfo.PlayerModel)
        self.viewModel.loadModel(self.classInfo.ViewModel)
        #self.animState.initGestureSlots()

        if giveWeapons:
            self.giveClassWeapons()

        if respawn:
            self.respawn(sendRespawn)

    def giveClassWeapons(self):
        from tf.weapon import WeaponRegistry
        for wpnId in self.classInfo.Weapons:
            wpnCls = WeaponRegistry.Weapons[wpnId]
            wpn = wpnCls()
            wpn.setPlayerId(self.doId)
            base.net.generateObject(wpn, self.zoneId)
            self.giveWeapon(wpn.doId, False)

    def stripWeapons(self):
        for wpnId in self.weapons:
            wpn = base.sv.doId2do.get(wpnId)
            if not wpn:
                continue
            base.sv.deleteObject(wpn)
        self.weapons = []
        self.activeWeapon = -1
        self.lastActiveWeapon = -1

    def setActiveWeapon(self, index):
        if self.activeWeapon == index:
            # Already the active weapon.
            return

        self.lastActiveWeapon = self.activeWeapon

        if self.activeWeapon >= 0 and self.activeWeapon < len(self.weapons):
            # Deactive the old weapon.
            wpnId = self.weapons[self.activeWeapon]
            wpn = base.sv.doId2do.get(wpnId)
            if wpn:
                wpn.deactivate()

        self.activeWeapon = index
        if self.activeWeapon < 0 or self.activeWeapon >= len(self.weapons):
            return

        # Activate the new weapon.
        wpnId = self.weapons[self.activeWeapon]
        wpn = base.sv.doId2do.get(wpnId)
        if wpn:
            wpn.activate()

    def giveWeapon(self, wpnId, makeActive = True):
        if wpnId in self.weapons:
            return

        wpn = base.sv.doId2do.get(wpnId)
        if wpn:
            wpn.setPlayerId(self.doId)

        self.weapons.append(wpnId)
        if makeActive or len(self.weapons) == 1:
            # Make it active if specifically requested or this is the only
            # weapon.
            self.setActiveWeapon(self.weapons.index(wpnId))

        self.emitSound("BaseCombatCharacter.AmmoPickup", client=self.owner)

    def getActiveWeapon(self):
        return self.activeWeapon

    def getAbsVelocity(self):
        return self.vel

    def getVelocity(self):
        """
        Returns local-space velocity.
        """
        quat = self.getQuat(NodePath())
        quat.invertInPlace()
        return quat.xform(self.vel)

    def announceGenerate(self):
        DistributedCharAI.announceGenerate(self)
        DistributedTFPlayerShared.announceGenerate(self)

    def generate(self):
        DistributedCharAI.generate(self)

        # Generate our view model as well.
        self.viewModel.setPlayerId(self.doId)
        self.viewModel.team = self.team
        self.viewModel.skin = self.skin
        base.sv.generateObject(self.viewModel, self.zoneId)

        base.air.lagComp.registerPlayer(self)

        # Start condition update logic.
        self.addTask(self.__conditionThinkAI, 'TFPlayerConditionThinkAI', appendTask=True, sim=True)

    def delete(self):
        if self.flag:
            self.flag.drop()

        # Get rid of the view model along with us.
        base.sv.deleteObject(self.viewModel)

        # Destroy all built objects.
        self.destroyAllObjects()

        # Delete all weapons.
        self.stripWeapons()

        base.game.playersByTeam[self.team].remove(self)

        base.air.lagComp.unregisterPlayer(self)

        DistributedCharAI.delete(self)
        DistributedTFPlayerShared.disable(self)

    def getCommandContext(self, i):
        assert i >= 0 and i < len(self.commandContexts)

        return self.commandContexts[i]

    def allocCommandContext(self):
        self.commandContexts.append(CommandContext())
        #if len(self.commandContexts) > 1000:
        #    self.notify.error("Too many command contexts")
        return self.commandContexts[len(self.commandContexts) - 1]

    def removeCommandContext(self, i):
        self.commandContexts.remove(self.commandContexts[i])

    def removeAllCommandContexts(self):
        self.commandContexts = []

    def removeAllCommandContextsExceptNewest(self):
        count = len(self.commandContexts)
        toRemove = count - 1
        if toRemove > 0:
            del self.commandContexts[0:toRemove]

        if len(self.commandContexts) == 0:
            # This shouldn't happen.
            assert False
            self.allocCommandContext()

        return self.commandContexts[0]

    def replaceContextCommands(self, ctx, commands, count):
        ctx.totalCmds = count
        ctx.droppedPackets = 0
        ctx.newCmds = []
        for i in range(count):
            ctx.newCmds.append(copy.deepcopy(commands[i]))
        ctx.cmds = ctx.newCmds
        ctx.backupCmds = []

    def determineSimulationTicks(self):
        ctxCount = len(self.commandContexts)

        simulationTicks = 0

        # Determine how much time we will be running this frmae and fixup
        # player clock as needed.
        for i in range(ctxCount):
            ctx = self.getCommandContext(i)
            assert ctx
            assert len(ctx.newCmds) > 0
            assert ctx.droppedPackets >= 0

            # Determine how long it will take to run those packets.
            simulationTicks += len(ctx.newCmds) + ctx.droppedPackets

        return simulationTicks

    def adjustPlayerTimeBase(self, simulationTicks):
        assert simulationTicks >= 0
        if simulationTicks < 0:
            return

        if base.sv.getMaxClients() == 1:
            # Set tickbase so that player simulation tick matches
            # base.sv.tickCount after all commands have been executed.
            self.tickBase = base.tickCount - simulationTicks + base.currentTicksThisFrame
        else:
            correctionSeconds = max(0.0, min(1.0, sv_clockcorrection_msecs.getValue() / 100.0))
            correctionTicks = base.timeToTicks(correctionSeconds)

            # Set the target tick correctionSeconds (rounded to ticks) ahead in
            # the future.  This way the client can alternate around this target
            # tick without getting smaller than base.sv.tickCount.  After
            # running the commands, simulation time should be equal or after
            # current base.sv.tickCount, otherwise the simulation time drops
            # out of the client side interpolated var history window.

            idealFinalTick = base.tickCount + correctionTicks
            estimatedFinalTick = self.tickBase + simulationTicks

            # If client gets ahead of this, we'll need to correct.
            tooFastLimit = idealFinalTick + correctionTicks
            # If the client gets behind this, we'll also need to correct.
            tooSlowLimit = idealFinalTick - correctionTicks

            # See if we are too fast.
            if estimatedFinalTick > tooFastLimit or estimatedFinalTick < tooSlowLimit:
                correctedTick = idealFinalTick - simulationTicks + base.currentTicksThisFrame
                self.tickBase = correctedTick

    def processPlayerCommands(self, backupCmds, newCmds, totalCommands, paused):
        ctx = self.allocCommandContext()
        assert ctx

        ctx.backupCmds = backupCmds
        ctx.newCmds = newCmds
        ctx.cmds = backupCmds + newCmds
        ctx.totalCmds = totalCommands
        ctx.paused = paused

        if ctx.paused:
            for cmd in ctx.cmds:
                cmd.buttons = InputFlag.Empty
                cmd.move = Vec3(0)
                cmd.viewAngles = self.viewAngles

            ctx.droppedPackets = 0

        self.paused = paused

        if paused:
            self.forceSimulation()
            self.simulate()

    def simulate(self):
        self.bulletForce = Vec3()

        DistributedCharAI.simulate(self)

        # Make sure to not simulate this guy twice per frame.
        if self.simulationTick == base.tickCount:
            return

        self.simulationTick = base.tickCount

        # See how many PlayerCommands are queued up for running.
        simulationTicks = self.determineSimulationTicks()

        # If some time will elapse, make sure our clock (self.tickBase) starts
        # at the correct time.
        if simulationTicks > 0:
            self.adjustPlayerTimeBase(simulationTicks)

        # Store off true server timestamps
        saveFrameTime = globalClock.frame_time
        saveDt = globalClock.dt

        commandContextCount = len(self.commandContexts)

        # Build a list of available commands.
        availableCommands = []

        # Contexts go from oldest to newest
        for i in range(commandContextCount):
            # Get oldest (newer are added to tail)
            ctx = self.getCommandContext(i)

            if len(ctx.cmds) == 0:
                continue

            numBackup = len(ctx.backupCmds)

            # If we haven't dropped too many packets, then run some commands
            if ctx.droppedPackets < 24:
                droppedCmds = ctx.droppedPackets

                # Run the last known cmd for each dropped cmd we don't have a
                # backup for.
                while droppedCmds > numBackup:
                    self.lastCmd.tickCount += 1
                    availableCommands.append(copy.deepcopy(self.lastCmd))
                    droppedCmds -= 1

                # Now run the "history" commands if we still have dropped packets.
                while droppedCmds > 0:
                    cmdNum = numBackup - droppedCmds
                    availableCommands.append(copy.deepcopy(ctx.backupCmds[cmdNum]))
                    droppedCmds -= 1

            # Now run any new commands.  Most recent command is at the tail.
            for i in range(len(ctx.newCmds)):
                availableCommands.append(copy.deepcopy(ctx.newCmds[i]))

            # Save off the last good command in case we drop > numBackup
            # packets and need to rerun them.  We'll use this to "guess" at
            # what was in the missing packets.
            self.lastCmd = copy.deepcopy(ctx.cmds[len(ctx.cmds) - 1])

        # base.currentTicksThisFrame == number of ticks remaining to be run, so
        # we should take the last N PlayerCommands and postpone them until the
        # next frame.

        # If we're running multiple ticks this frame, don't peel off all of the
        # commands, spread them out over the server ticks.  Use blocks of two
        # in alternate ticks.

        # False would be sv_alternateticks, if I want to implement that.
        cmdLimit = 2 if False else 1
        cmdsToRun = len(availableCommands)
        if base.currentTicksThisFrame >= cmdLimit and len(availableCommands) > cmdLimit:
            cmdsToRollOver = min(len(availableCommands), base.currentTicksThisFrame - 1)#

            cmdsToRun = len(availableCommands) - cmdsToRollOver
            assert cmdsToRun >= 0

            # Clear all contexts except last one.
            if cmdsToRollOver > 0:
                ctx = self.removeAllCommandContextsExceptNewest()
                self.replaceContextCommands(ctx, availableCommands, cmdsToRollOver)
            else:
                # Clear all contexts
                self.removeAllCommandContexts()
        else:
            # Clear all contexts.
            self.removeAllCommandContexts()

        # Now run the commands.
        if cmdsToRun > 0:
            for i in range(cmdsToRun):
                self.runPlayerCommand(availableCommands[i], base.deltaTime)

        # Restore the true server clock.
        base.setFrameTime(saveFrameTime)
        base.setDeltaTime(saveDt)

    def runPlayerCommand(self, cmd, deltaTime):
        self.currentCommand = cmd

        base.setFrameTime(self.tickBase * base.intervalPerTick)
        base.setDeltaTime(base.intervalPerTick)

        base.net.predictionRandomSeed = cmd.randomSeed

        if not self.isDead():

            # Do weapon selection.
            if cmd.weaponSelect >= 0 and cmd.weaponSelect < len(self.weapons) and cmd.weaponSelect != self.activeWeapon:
                self.setActiveWeapon(cmd.weaponSelect)

            self.updateButtonsState(cmd.buttons)

            self.viewAngles = cmd.viewAngles
            self.eyeH = self.viewAngles[0] % 360 / 360
            self.eyeP = self.viewAngles[1] % 360 / 360

            # Get the active weapon
            wpn = None
            if self.activeWeapon != -1:
                wpnId = self.weapons[self.activeWeapon]
                wpn = base.sv.doId2do.get(wpnId)

            if wpn:
                wpn.itemPreFrame()

            # Run the movement.
            DistributedTFPlayerShared.runPlayerCommand(self, cmd, deltaTime)

            if wpn:
                wpn.itemBusyFrame()

            self.notify.debug("Running command %s" % str(cmd))

            if wpn:
                wpn.itemPostFrame()

            self.animState.update()

        # Let time pass.
        self.tickBase += 1

        # Store off the command number of this command so we can inform the
        # client that we ran it.
        self.lastRunCommandNumber = max(self.lastRunCommandNumber, cmd.commandNumber)

        #print("Server ran command", cmd.commandNumber, "at pos", self.getPos())

        base.net.predictionRandomSeed = 0
        self.currentCommand = None

    def playerCommand(self, data):
        """ Player command sent to us by the client. """

        client = base.sv.clientSender

        dg = Datagram(data)
        dgi = DatagramIterator(dg)

        if self.lastMovementTick == base.tickCount:
            self.notify.debug("Received more than one command this tick")
            return

        backupCommands = dgi.getUint8()
        newCommands = dgi.getUint8()
        totalCommands = newCommands + backupCommands

        self.notify.debug("Got %i new cmds and %i backup cmds" % (newCommands, backupCommands))

        backupCmds = []
        newCmds = []

        assert newCommands >= 0
        assert (totalCommands - newCommands) >= 0

        if totalCommands < 0 or totalCommands >= (self.MaxCMDBackup - 1):
            self.notify.warning("Too many cmds (%i) sent to us from client %i" % (totalCommands, client.id))
            return

        nullCmd = PlayerCommand()
        prev = nullCmd
        # Backups come first
        for i in range(backupCommands):
            self.notify.debug("Reading backup cmd %i" % i)
            to = PlayerCommand.readDatagram(dgi, prev)
            backupCmds.append(to)
            prev = to
        # Now the new commands
        for i in range(newCommands):
            self.notify.debug("Reading new cmd %i" % i)
            to = PlayerCommand.readDatagram(dgi, prev)
            newCmds.append(to)
            prev = to

        self.processPlayerCommands(backupCmds, newCmds, totalCommands, False)

    def getTimeBase(self):
        return self.tickBase * base.intervalPerTick

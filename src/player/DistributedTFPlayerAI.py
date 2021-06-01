
from tf.character.DistributedCharAI import DistributedCharAI
from direct.distributed2.ServerConfig import *
from .DistributedTFPlayerShared import DistributedTFPlayerShared

from direct.directnotify.DirectNotifyGlobal import directNotify

from .PlayerCommand import PlayerCommand
from .InputButtons import InputFlag
from .TFPlayerAnimStateAI import TFPlayerAnimStateAI
from .PlayerAnimEvent import PlayerAnimEvent
from .TFClass import *
from .DViewModelAI import DViewModelAI
from tf.weapon.TakeDamageInfo import TakeDamageInfo, calculateBulletDamageForce, addMultiDamage

from tf.tfbase import TFGlobals
from tf.tfbase.TFGlobals import Contents, CollisionGroup, TakeDamage, DamageType

from panda3d.core import Datagram, DatagramIterator, Vec3, Point3, NodePath
from panda3d.pphysics import PhysRayCastResult, PhysQueryNodeFilter

import copy
import random

tf_damage_range = 0.5
tf_damageforcescale_other = 3.0

class CommandContext:
    def __init__(self):
        self.cmds = []
        self.numCmds = 0
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
        self.tickBase = 0
        self.simulationTick = 0
        self.paused = False
        self.lastCmd = PlayerCommand()
        self.viewAngles = Vec3(0, 0, 0)
        self.isDead = False
        self.nextAttack = 0.0
        self.forceJoint = -1
        self.bulletForce = Vec3(0)

        # Also give them a view model
        self.viewModel = DViewModelAI()

    def getWorldSpaceCenter(self):
        return self.getPos(NodePath()) + (0, 0, self.classInfo.ViewHeight / 2)

    def getClassSize(self):
        mins = self.classInfo.BBox[0]
        maxs = self.classInfo.BBox[1]
        return Vec3(maxs[0] - mins[0], maxs[1] - mins[1], maxs[2] - mins[2])

    def onTakeDamage_alive(self, info):
        vecDir = Vec3(0)
        if info.inflictor:
            vecDir = info.inflictor.getWorldSpaceCenter() - Vec3(0, 0, 10) - self.getWorldSpaceCenter()
            vecDir.normalize()

        force = vecDir * -self.damageForce(self.getClassSize(), info.damage, tf_damageforcescale_other)
        self.velocity += force

        self.health -= int(info.damage + 0.5)
        self.health = max(0, self.health)
        if self.health <= 0:
            # Died.
            self.die(info.attacker, info)

    def damageForce(self, size, damage, scale):
        force = damage * ((48 * 48 * 82.0) / (size[0] * size[1] * size[2])) * scale
        if force > 1000:
            force = 1000
        return force

    def onTakeDamage(self, inputInfo):
        info = inputInfo#copy.deepcopy(inputInfo)

        if not info.damage:
            return

        if self.isDead:
            return

        healthBefore = self.health
        if not base.game.playerCanTakeDamage(self, info.attacker):
            return

        # Save damage force for ragdolls.
        self.bulletForce = Vec3(info.damageForce)
        #self.bulletForce[0] = max(-15000, min(15000, self.bulletForce[0]))
        #self.bulletForce[1] = max(-15000, min(15000, self.bulletForce[1]))
        #self.bulletForce[2] = max(-15000, min(15000, self.bulletForce[2]))

        # If we're not damaging ourselves, apply randomness
        if info.attacker != self and not (info.damageType & (DamageType.Drown | DamageType.Fall)):
            damage = 0
            randomDamage = info.damage * tf_damage_range#.getValue()
            minFactor = 0.25
            maxFactor = 0.75
            if info.damageType & DamageType.UseDistanceMod:
                distance = max(1.0, (self.getWorldSpaceCenter() - info.attacker.getWorldSpaceCenter()).length())
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

        self.onTakeDamage_alive(info)

        if self.health > 0:
            # If still alive, flinch
            self.doAnimationEvent(PlayerAnimEvent.Flinch)

        self.sendUpdate('pain')

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

        attacker = info.attacker
        if attacker:
            # Prevent team damage so blood doesn't appear.
            if not base.game.playerCanTakeDamage(self, attacker):
                return

        addMultiDamage(info, self)

    def fireBullet(self, info, doEffects, damageType, customDamageType):
        # Fire a bullet (ignoring the shooter).
        start = info['src']
        #end = start + info['dirShooting'] * info['distance']
        result = PhysRayCastResult()
        filter = PhysQueryNodeFilter(self, PhysQueryNodeFilter.FTExclude)
        base.physicsWorld.raycast(result, start, info['dirShooting'], info['distance'],
                                  BitMask32(Contents.HitBox | Contents.Solid), BitMask32.allOff(),
                                  CollisionGroup.Empty, filter)
        print("Fire bullet", start, "to", info['dirShooting'] * info['distance'])
        if result.hasBlock():
            # Bullet hit something!
            print("\tHit something")
            block = result.getBlock()
            actor = block.getActor()
            entity = actor.getPythonTag("entity")
            if not entity:
                # Didn't hit an entity.  Hmm.
                return

            if doEffects:
                # TODO
                pass

            if not IS_CLIENT:
                print("\t\tHit entity", NodePath(actor))
                # Server-specific.
                dmgInfo = TakeDamageInfo(self, self, info['damage'], damageType)
                dmgInfo.customDamage = customDamageType
                calculateBulletDamageForce(dmgInfo, block.getPosition() - info['src'], block.getPosition(), 1.0)
                entity.dispatchTraceAttack(dmgInfo, info['dirShooting'], block)

    def doAnimationEvent(self, event, data = 0):
        self.animState.doAnimationEvent(event, data)

    def doClassSpecialSkill(self):
        pass

    def die(self, killer, info):
        self.isDead = True
        # Become a ragdoll.
        self.sendUpdate('becomeRagdoll', [self.character.findJoint("bip_pelvis"), info.sourcePosition, self.bulletForce])
        # Respawn after 5 seconds.
        self.addTask(self.respawnTask, 'respawn', appendTask = True)

    def respawnTask(self, task):
        if task.time < 5.0:
            # Not ready to respawn yet.
            return task.cont

        # Refill health
        self.health = self.maxHealth
        # Refill ammo
        for wpnId in self.weapons:
            wpn = base.net.doId2do.get(wpnId)
            wpn.ammo = wpn.maxAmmo
            wpn.clip = wpn.maxClip
        # Set to the primary weapon
        self.setActiveWeapon(0)
        self.setPos(Point3(random.uniform(-128, 128), random.uniform(-128, 128), 0))
        self.setHpr(Vec3(random.uniform(-180, 180), 0, 0))
        self.isDead = False
        self.sendUpdate('respawn')
        return task.done

    def changeClass(self, cls):
        self.stripWeapons()
        self.tfClass = cls
        self.classInfo = ClassInfos[self.tfClass]
        self.maxHealth = self.classInfo.MaxHealth
        self.health = self.maxHealth
        self.setModel(self.classInfo.PlayerModel)
        self.animState.initGestureSlots()

    def stripWeapons(self):
        for wpnId in self.weapons:
            wpn = base.sv.doId2do.get(wpnId)
            if not wpn:
                continue
            base.sv.deleteObject(wpn)
        self.weapons = []
        self.activeWeapon = -1

    def setActiveWeapon(self, index):
        if self.activeWeapon > 0 and self.activeWeapon < len(self.weapons):
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
        self.reparentTo(base.render)

    def generate(self):
        # Generate our view model as well.
        self.viewModel.setPlayerId(self.doId)
        base.sv.generateObject(self.viewModel, self.zoneId)

    def delete(self):
        # Get rid of the view model along with us.
        base.sv.deleteObject(self.viewModel)

        DistributedCharAI.delete(self)
        DistributedTFPlayerShared.disable(self)

    def getCommandContext(self, i):
        assert i >= 0 and i < len(self.commandContexts)

        return self.commandContexts[i]

    def allocCommandContext(self):
        self.commandContexts.append(CommandContext())
        if len(self.commandContexts) > 1000:
            self.notify.error("Too many command contexts")
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
        ctx.numCmds = count
        ctx.totalCmds = count
        ctx.droppedPackets = 0
        # Add them in so the most recent is at slot 0.
        ctx.cmds = []
        for i in reversed(range(count)):
            ctx.cmds.append(copy.deepcopy(commands[i]))

    def determineSimulationTicks(self):
        ctxCount = len(self.commandContexts)

        simulationTicks = 0

        # Determine how much time we will be running this frmae and fixup
        # player clock as needed.
        for i in range(ctxCount):
            ctx = self.getCommandContext(i)
            assert ctx
            assert ctx.numCmds > 0
            assert ctx.droppedPackets >= 0

            # Determine how long it will take to run those packets.
            simulationTicks += ctx.numCmds + ctx.droppedPackets

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

    def processPlayerCommands(self, cmds, newCommands, totalCommands, paused):
        ctx = self.allocCommandContext()
        assert ctx

        ctx.cmds = list(reversed(cmds))
        ctx.numCmds = newCommands
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
        self.bulletForce = Vec3(0)

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
        saveFrameTime = globalClock.getFrameTime()
        saveDt = globalClock.getDt()

        commandContextCount = len(self.commandContexts)

        # Build a list of available commands.
        availableCommands = []

        # Contexts go from oldest to newest
        for i in range(commandContextCount):
            # Get oldest (newer are added to tail)
            ctx = self.getCommandContext(i)

            if len(ctx.cmds) == 0:
                continue

            numBackup = ctx.totalCmds - ctx.numCmds

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
                    cmdNum = ctx.numCmds + droppedCmds - 1
                    availableCommands.append(copy.deepcopy(ctx.cmds[cmdNum]))
                    droppedCmds -= 1

            # Now run any new commands.  Go backward because the most recent
            # command is at index 0.
            for i in reversed(range(ctx.numCmds)):
                availableCommands.append(copy.deepcopy(ctx.cmds[i]))

            # Save off the last good command in case we drop > numBackup
            # packets and need to rerun them.  We'll use this to "guess" at
            # what was in the missing packets.
            self.lastCmd = copy.deepcopy(ctx.cmds[0])

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
            cmdsToRollOver = min(len(availableCommands), base.currentTicksThisFrame - 1)

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
        globalClock.setFrameTime(saveFrameTime)
        globalClock.setDt(saveDt)
        base.frameTime = saveFrameTime
        base.deltaTime = saveDt

    def runPlayerCommand(self, cmd, deltaTime):
        if self.isDead:
            return

        if cmd.weaponSelect >= 0 and cmd.weaponSelect < len(self.weapons) and cmd.weaponSelect != self.activeWeapon:
            print("Change active weapon to", cmd.weaponSelect)
            self.setActiveWeapon(cmd.weaponSelect)

        # Get the active weapon
        wpn = None
        if self.activeWeapon != -1:
            wpnId = self.weapons[self.activeWeapon]
            wpn = base.sv.doId2do.get(wpnId)

        if wpn:
            wpn.itemPreFrame()

        # Run the movement.
        DistributedTFPlayerShared.runPlayerCommand(self, cmd, deltaTime)

        self.buttons = cmd.buttons

        self.notify.debug("Running command %s" % str(cmd))

        self.viewAngles = cmd.viewAngles

        if wpn:
            wpn.itemPostFrame()

        self.animState.update()

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

        cmds = []

        assert newCommands >= 0
        assert (totalCommands - newCommands) >= 0

        if totalCommands < 0 or totalCommands >= (self.MaxCMDBackup - 1):
            self.notify.warning("Too many cmds (%i) sent to us from client %i" % (totalCommands, client.id))
            return

        nullCmd = PlayerCommand()
        prev = nullCmd
        for i in range(totalCommands - 1, -1, -1):
            self.notify.debug("Reading cmd %i" % i)
            to = PlayerCommand.readDatagram(dgi, prev)
            cmds.insert(i, to)
            prev = to

        self.processPlayerCommands(cmds, newCommands, totalCommands, False)

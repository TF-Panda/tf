"""Prediction module: contains the Prediction class"""

from panda3d.core import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.DirectObject import DirectObject

import copy

from tf.movement.GameMovement import g_game_movement

cl_predictweapons = ConfigVariableBool("cl-predict-weapons", True)
cl_pred_optimize = ConfigVariableInt("cl-pred-optimize", 2)
cl_idealpitchscale = ConfigVariableDouble("cl-ideal-pitch-scale", 0.8)
cl_predict = ConfigVariableBool("cl-predict", True)
cl_show_error = ConfigVariableBool("cl-show-pred-errors", False)

PREDICTION_DATA_SLOTS = 90

PREDICTION_COPY_EVERYTHING = 0
PREDICTION_COPY_NON_NETWORKED_ONLY = 1
PREDICTION_COPY_NETWORKED_ONLY = 2

PREDICTION_DIFF_DIFFERS = 0
PREDICTION_DIFF_IDENTICAL = 1
PREDICTION_DIFF_WITHIN_TOLERANCE = 2

PREDICTION_TABLE_ENTITY = 0
PREDICTION_TABLE_DICT = 1

PREDICTION_ON_EPSILON = 0.1
PREDICTION_MAX_FORWARD = 6.0
PREDICTION_MIN_CORRECTION_DISTANCE = 0.25
PREDICTION_MIN_EPSILON = 0.5
PREDICTION_MAX_ERROR = 64.0

class PredictionField:

    def __init__(self, name, type, getter = None, setter = None, private = False, networked = True,
                 noErrorCheck = False, tolerance = 0.0):
        self.name = name
        self.type = type
        self.getter = getter
        self.setter = setter
        self.private = private
        self.networked = networked
        self.noErrorCheck = noErrorCheck
        self.tolerance = tolerance

class PredictionCopy:

    notify = directNotify.newCategory("PredictionCopy")

    def __init__(self, type, dest, src, countErrors = False,
                 reportErrors = False, performCopy = True):
        self.type = type
        self.dest = dest
        if isinstance(dest, dict):
            self.destType = PREDICTION_TABLE_DICT
        else:
            self.destType = PREDICTION_TABLE_ENTITY
        self.src = src
        if isinstance(src, dict):
            self.srcType = PREDICTION_TABLE_DICT
        else:
            self.srcType = PREDICTION_TABLE_ENTITY
        self.errorCheck = countErrors
        self.reportErrors = reportErrors
        self.performCopy = performCopy
        self.errorCount = 0

    def getValue(self, fieldName, table, tableType, data):
        if tableType == PREDICTION_TABLE_DICT:
            return table[fieldName]
        else:
            if data.getter:
                return data.getter()
            else:
                return getattr(table, fieldName)

    def setValue(self, fieldName, table, tableType, data, value):
        if tableType == PREDICTION_TABLE_DICT:
            table[fieldName] = data.type(value)
        else:
            if data.setter:
                data.setter(data.type(value))
            else:
                setattr(table, fieldName, data.type(value))

    def compareFloat(self, outValue, inValue, data):
        tolerance = data.tolerance
        useTolerance = (tolerance > 0.0)

        if outValue == inValue:
            return PREDICTION_DIFF_IDENTICAL
        elif useTolerance and abs(outValue - inValue) <= tolerance:
            return PREDICTION_DIFF_WITHIN_TOLERANCE
        else:
            return PREDICTION_DIFF_DIFFERS

    def getDiffType(self, destValue, srcValue, data):
        if not self.errorCheck:
            return PREDICTION_DIFF_DIFFERS

        difftype = PREDICTION_DIFF_IDENTICAL

        if not data.noErrorCheck:
            if data.type == float:
                difftype = self.compareFloat(destValue, srcValue, data)

            elif data.type in (str, bool, int):
                if destValue != srcValue:
                    difftype = PREDICTION_DIFF_DIFFERS

            elif data.type in (Vec3, Point3, Quat, Vec4):
                tolerance = data.tolerance
                differs = destValue != srcValue
                if differs and tolerance > 0.0:
                    delta = destValue - srcValue
                    difftype = PREDICTION_DIFF_WITHIN_TOLERANCE
                    for i in range(len(delta)):
                        if abs(delta[i]) > tolerance:
                            difftype = PREDICTION_DIFF_DIFFERS
                            break
                elif differs:
                    difftype = PREDICTION_DIFF_DIFFERS
            else:
                self.notify.error("Unknown field type " + repr(data.type))

        return difftype

    def transferData(self, operation, dataDesc, destSlot = -1):
        """
        Copies differing prediction fields from src to dest and counts the
        number of errors (fields differing and outside tolerance).
        """

        for fieldName, data in dataDesc.items():
            if data.private:
                continue
            if self.type == PREDICTION_COPY_NON_NETWORKED_ONLY and data.networked:
                continue
            if self.type == PREDICTION_COPY_NETWORKED_ONLY and not data.networked:
                continue

            srcValue = self.getValue(fieldName, self.src, self.srcType, data)
            destValue = self.getValue(fieldName, self.dest, self.destType, data)

            difftype = self.getDiffType(destValue, srcValue, data)

            if self.performCopy and difftype != PREDICTION_DIFF_IDENTICAL:
                self.setValue(fieldName, self.dest, self.destType, data, srcValue)
            if self.errorCheck and difftype == PREDICTION_DIFF_DIFFERS:
                if self.reportErrors:
                    self.reportError(fieldName, srcValue, destValue, data, destSlot)
                self.errorCount += 1

        return self.errorCount

    def reportError(self, fieldName, srcValue, destValue, data, destSlot):
        predCommand = base.net.prediction.currentCommandReference + destSlot
        if data.type in (str, bool):
            self.notify.info(f"{fieldName} differs (command {predCommand}): pred {destValue}, net {srcValue}")
        else:
            self.notify.info(f"{fieldName} differs (command {predCommand}): pred {destValue}, net {srcValue}, delta {destValue - srcValue}")

class Prediction(DirectObject):
    """
    This class does the heavy lifting of implementing client-side prediction.
    """

    notify = directNotify.newCategory("Prediction")

    def __init__(self):
        DirectObject.__init__(self)
        self.inPrediction = False
        self.firstTimePredicted = False
        self.incomingPacketNumber = 0
        self.idealPitch = 0.0
        self.previousStartFrame = -1
        self.numCommandsPredicted = 0
        self.numServerCommandsAcknowledged = 0
        self.currentCommandReference = 0
        self.previousAckHadErrors = False

        # List of all entities that use prediction.
        self.predictables = []

    def addPredictable(self, ent):
        assert ent not in self.predictables
        self.predictables.append(ent)

    def removePredictable(self, ent):
        if ent in self.predictables:
            self.predictables.remove(ent)

    def checkError(self, commandsAcked):
        """
        Checks for prediction errors.
        """
        if not cl_predict.getValue():
            return

        slot = base.localAvatar.getPredictedFrame(commandsAcked - 1)
        netPos = base.localAvatar.getPos()
        # Compare what the server returned with what we had predicted it to be.
        predictedPos = slot.get("pos")
        if predictedPos is None:
            return
        delta = predictedPos - netPos
        length = delta.length()
        #self.notify.info(f"For slot {commandsAcked - 1}, predicted pos: {predictedPos}, net pos: {netPos}")
        if length > PREDICTION_MAX_ERROR:
            # A teleport or something, clear out error.
            length = 0.0
        else:
            if length > PREDICTION_MIN_EPSILON:
                # Difference is outside tolerance but within an acceptable
                # amount to smooth it out.
                self.notify.info("Prediction error %6.3f units (%6.3f %6.3f %6.3f)" %
                    (length, delta[0], delta[1], delta[2]))


    def preEntityPacketReceived(self, commandsAcked, currentWorldUpdatePacket):

        # Cache off incoming packet #
        self.incomingPacketNumber = currentWorldUpdatePacket

        if not cl_predict.getValue():
            return

        if not hasattr(base, 'localAvatar') or not base.localAvatar:
            return

        # Transfer intermediate data from other predictables.
        for p in self.predictables:
            if p.predictable:
                p.preEntityPacketReceived(commandsAcked)

    def postEntityPacketReceived(self):
        if not cl_predict.getValue():
            return

        # Transfer intermediate data from other predictables.
        for p in self.predictables:
            if not p.predictable:
                continue
            p.postEntityPacketReceived()

    def onReceivedUncompressedPacket(self):
        self.numCommandsPredicted = 0
        self.numServerCommandsAcknowledged = 0
        self.previousStartFrame = -1

    def postNetworkDataReceived(self, commandsAcknowledged):
        """
        Called at the end of the frame if any packets were received.
        """

        errorCheck = (commandsAcknowledged > 0)

        self.numServerCommandsAcknowledged += commandsAcknowledged
        self.previousAckHadErrors = False

        if not hasattr(base, 'localAvatar') or not base.localAvatar:
            return

        if cl_predict.getValue():
            # Transfer intermediate data from other predictables.
            for p in self.predictables:
                if p.predictable:
                    if p.postNetworkDataReceived(self.numServerCommandsAcknowledged):
                        self.previousAckHadErrors = True

            if errorCheck:
                self.checkError(self.numServerCommandsAcknowledged)

    def restoreOriginalEntityState(self):
        """
        Restores all predicted entities to their most recently networked state.
        """
        for p in self.predictables:
            if p.predictable:
                p.restoreData("RestoreOriginalEntityState", -1, PREDICTION_COPY_EVERYTHING)

    def restoreEntityToPredictedFrame(self, frame):
        if not hasattr(base, 'localAvatar') or not base.localAvatar:
            return

        if not cl_predict.getValue():
            return

        for p in self.predictables:
            if p.predictable:
                p.restoreData("RestoreEntityToPredictedFrame", frame, PREDICTION_COPY_EVERYTHING)

    def shiftIntermediateDataForward(self, slotsToRemove, numberOfCommandsRun):
        if not cl_predict.getValue():
            return

        for p in self.predictables:
            if not p.predictable:
                continue
            p.shiftIntermediateDataForward(slotsToRemove, numberOfCommandsRun)

    def storePredictionResults(self, slot):
        for p in self.predictables:
            if not p.predictable:
                continue
            p.saveData("StorePredictionResults", slot, PREDICTION_COPY_EVERYTHING)

    def computeFirstCommandToExecute(self, receivedNewWorldUpdate, incomingAcknowledged, outgoingCommand):
        destinationSlot = 1
        skipAhead = 0

        # If we didn't receive a new update (or we received an update that didn't ack any PlayerCommands
        # so for the player it should be just like receiving no update), just jump right up to the very
        # last command we creaetd for this very frame since we probably wouldn't have had any errors
        # without being notified by the server of such a case.
        if (not receivedNewWorldUpdate) or (not self.numServerCommandsAcknowledged):
            # This is where we would normally start.
            start = incomingAcknowledged + 1
            # outgoingCommand is where we really want to start.
            skipAhead = max(0, outgoingCommand - start)
            # Don't start past the last predicted command, though, or we'll get prediction errors.
            skipAhead = min(skipAhead, self.numCommandsPredicted)

            # Always restore since otherwise we might start prediction using an "interpolated" value instead of
            # a purely predicted value.
            self.restoreEntityToPredictedFrame(skipAhead - 1)

            #print("%i/%i no world, skip to %i restore from slot %i" %
            #    (globalClock.getFrameCount(),
            #     base.tickCount,
            #     skipAhead,
            #     skipAhead - 1))
        else:
            # Otherwise, there is a second optimization, wherein if we did receive an update, but no
            # values differed (or were outside their epsilon) and the server actually acknlowledged running
            # one or more commands, then we can revert the entity to the predicted state from last frame,
            # shift the # of commands worth of intermediate state off of front the intermediate state array,
            # and only predict the PlayerCommand from the latest render frame.
            if (cl_pred_optimize.getValue() >= 2) and \
                (not self.previousAckHadErrors) and \
                (self.numCommandsPredicted > 0) and \
                (self.numServerCommandsAcknowledged <= self.numCommandsPredicted):

                # Copy all of the previously predicted data back into entity so we can skip
                # repredicting it.  This is the final slot that we previously predicted.
                self.restoreEntityToPredictedFrame(self.numCommandsPredicted - 1)

                # Shift intermediate state blocks down by # of commands ack'd
                self.shiftIntermediateDataForward(self.numServerCommandsAcknowledged, self.numCommandsPredicted)

                # Only predict new commands (note, this should be the same number that we could compute
                # above based on outgoingCommand - incomingAcknowleged - 1).
                skipAhead = (self.numCommandsPredicted - self.numServerCommandsAcknowledged)

                #print("%i/%i optimize2, skip to %i restore from slot %i" %
                #    (globalClock.getFrameCount(),
                #    base.tickCount,
                #    skipAhead,
                #    self.numCommandsPredicted - 1))
            else:
                if self.previousAckHadErrors:
                    # If an entity gets a prediction error, then we want to clear out its interpolated variables
                    # so we don't mix different samples at the same timestamps.  We subtract 1 tick interval
                    # here because if we don't, we'll have 3 interpolation entries with the same timestamp as
                    # this predicted frame, so we don't be able to interpolate (which leads to jerky movement)
                    # in the player when ANY entity like your gun gets a prediction error).
                    prev = globalClock.getFrameTime()
                    base.setFrameTime((base.localAvatar.tickBase * base.intervalPerTick) - base.intervalPerTick)

                    for p in self.predictables:
                        p.resetInterpolatedVars()

                    base.setFrameTime(prev)

        destinationSlot += skipAhead
        # Always reset these values now that we handled them.
        self.numCommandsPredicted = 0
        self.previousAckHadErrors = False
        self.numServerCommandsAcknowledged = 0

        return destinationSlot

    def performPrediction(self, receivedNewWorldUpdate, localAvatar, incomingAcknowledged, outgoingCommand):
        self.inPrediction = True

        i = self.computeFirstCommandToExecute(receivedNewWorldUpdate, incomingAcknowledged, outgoingCommand)
        assert i >= 1
        while True:
            # incomingAcknowledged is the last PlayerCommand the server acknowledged
            # having acted upon.
            currentCommand = incomingAcknowledged + i

            # We've caught up to the current command.
            if currentCommand > outgoingCommand:
                break

            if i >= PREDICTION_DATA_SLOTS:
                break

            cmd = base.localAvatar.getCommand(currentCommand)
            if not cmd:
                break

            # Is this the first time predicting this?
            self.firstTimePredicted = not cmd.hasBeenPredicted

            # Set globals appropriately
            frameTime = base.localAvatar.tickBase * base.intervalPerTick

            self.runSimulation(currentCommand, frameTime, cmd, base.localAvatar)

            base.setFrameTime(frameTime)
            base.setDeltaTime(base.intervalPerTick)

            # Call untouch on any entities no longer predicted to be touching.
            #self.untouch() # TODO

            # Store intermediate data into appropriate slot.
            self.storePredictionResults(i - 1) # Note that i starts at 1

            self.numCommandsPredicted = i

            if currentCommand == outgoingCommand:
                base.localAvatar.finalPredictedTick = base.localAvatar.tickBase

            # Mark that we issued any needed sounds, if not done already.
            cmd.hasBeenPredicted = True

            # Copy the state over.
            i += 1

        self.inPrediction = False

        # Somehow we looped past the end of the list (severe lag), don't predict at all.
        if i > PREDICTION_DATA_SLOTS:
            return False

        return True

    def runSimulation(self, currentCommand, frameTime, cmd, localAvatar):
        ctx = localAvatar.commandContext
        ctx.needsProcessing = True
        ctx.cmd = cmd
        ctx.commandNumber = currentCommand

        # Make sure simulation occurs at most once per entity per PlayerCommand.
        for p in self.predictables:
            p.simulationTick = -1

        # Don't used cache
        for i in range(len(self.predictables)):
            # Always reset.
            base.setFrameTime(frameTime)
            base.setDeltaTime(base.intervalPerTick)

            p = self.predictables[i]
            if not p:
                continue

            isLocal = (localAvatar == p)
            # Local avatar simulates first, if this assert firs then the predictables
            # list isn't sorted correctly.
            if isLocal:
                assert i == 0

            if p.playerSimulated:
                continue

            # TODO: client-created entities
            #if p.clientCreated:
            #   if not self.firstTimePredicted:
            #       continue
            #   p.simulate()
            #else:
            p.simulate()

            # Don't update last networked data here!!!
            p.onLatchInterpolatedVars(globalClock.getFrameTime(),
                                      p.SimulationVar | p.AnimationVar | p.OmitUpdateLastNetworked)

    def setupMove(self, avatar, cmd):
        """
        Fills in the avatar's MoveData structure for the upcoming move.
        """
        move = avatar.moveData
        move.firstRunOfFunctions = self.firstTimePredicted
        move.player = avatar
        move.velocity = Vec3(avatar.velocity[0], avatar.velocity[1], avatar.velocity[2])
        #print("IN velocity", move.velocity)
        move.origin = avatar.getPos()
        move.oldAngles = Vec3(move.angles)
        move.oldButtons = avatar.lastButtons
        move.clientMaxSpeed = avatar.maxSpeed
        move.angles = cmd.viewAngles
        move.viewAngles = cmd.viewAngles
        move.buttons = avatar.buttons
        move.onGround = avatar.onGround

        move.forwardMove = cmd.move[1]
        move.sideMove = cmd.move[0]
        move.upMove = cmd.move[2]

    def finishMove(self, avatar, cmd):
        """
        Stores results of the previous move onto the avatar.
        """
        move = avatar.moveData
        avatar.velocity = Vec3(move.velocity)
        #print("OUT velocity", avatar.velocity)
        #avatar.networkPos = Point3(move.origin)
        avatar.oldButtons = move.buttons
        avatar.onGround = move.onGround
        avatar.maxSpeed = move.clientMaxSpeed
        avatar.setPos(move.origin)

    def runCommand(self, avatar, cmd):
        if avatar.isDead():
            return

        self.startCommand(avatar, cmd)

        # Set globals appropriately
        base.setFrameTime(avatar.tickBase * base.intervalPerTick)
        base.setDeltaTime(base.intervalPerTick)

        # Do weapon selection
        if cmd.weaponSelect >= 0 and cmd.weaponSelect < len(avatar.weapons) and cmd.weaponSelect != avatar.activeWeapon:
            avatar.setActiveWeapon(cmd.weaponSelect)

        avatar.updateButtonsState(cmd.buttons)

        oldAngles = Vec3(avatar.viewAngles)

        avatar.viewAngles = cmd.viewAngles

        #self.runPreThink(avatar)
        #self.runThink(avatar, base.intervalPerTick)

        # Get the active weapon
        wpn = None
        if avatar.activeWeapon != -1:
            wpnId = avatar.weapons[avatar.activeWeapon]
            wpn = base.net.doId2do.get(wpnId)

        if wpn:
            wpn.itemPreFrame()

        # Setup input.
        self.setupMove(avatar, cmd)

        avatar.controller.setFootPosition(avatar.getPos())

        g_game_movement.processMovement(avatar, avatar.moveData)

        if wpn:
            wpn.itemBusyFrame()

        self.finishMove(avatar, cmd)

        #self.runPostThink(avatar)
        if wpn:
            wpn.itemPostFrame()

        self.finishCommand(avatar)

        # Restore smooth view angles.
        avatar.viewAngles = oldAngles

        avatar.tickBase += 1

    def startCommand(self, avatar, cmd):
        avatar.currentCommand = cmd
        base.net.predictionRandomSeed = cmd.randomSeed
        base.net.predictionPlayer = avatar

    def finishCommand(self, avatar):
        avatar.currentCommand = None
        base.net.predictionRandomSeed = 0
        base.net.predictionPlayer = None

    def update(self, startFrame, validFrame, incomingAcknowledged, outgoingCommand):
        self.currentCommandReference = incomingAcknowledged

        receivedNewWorldUpdate = True

        # Still starting at same frame, so make sure we don't do extra
        # prediction.
        if (self.previousStartFrame == startFrame) and \
            cl_pred_optimize.getValue() and \
            cl_predict.getValue():

            receivedNewWorldUpdate = False

        self.previousStartFrame = startFrame

        # Save off current timer values.
        saveDeltaTime = globalClock.getDt()
        saveFrameTime = globalClock.getFrameTime()
        saveFrameCount = globalClock.getFrameCount()

        self.doUpdate(receivedNewWorldUpdate, validFrame, incomingAcknowledged, outgoingCommand)

        # Restore true timer values.
        base.setFrameTime(saveFrameTime)
        base.setDeltaTime(saveDeltaTime)
        base.setFrameCount(saveFrameCount)

    def doUpdate(self, receivedNewWorldUpdate, validFrame, incomingAcknowledged, outgoingCommand):
        if not hasattr(base, 'localAvatar') or not base.localAvatar:
            return

        if not validFrame:
            return

        if receivedNewWorldUpdate:
            self.restoreOriginalEntityState()

        if not self.performPrediction(receivedNewWorldUpdate, base.localAvatar, incomingAcknowledged, outgoingCommand):
            return

"""LagCompensation module: contains the LagCompensation class."""

from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify

from panda3d.core import *

maxUnlag = 1.0

#tf_server_lag_comp_debug = ConfigVariableBool("tf-server-lag-comp-debug", False)

class PlayerSample:
    pass

class PlayerRecord:

    def __init__(self, doId):
        self.doId = doId
        self.track = []
        self.needsRestore = False
        self.restore = PlayerSample()
        self.change = PlayerSample()

class LagCompensation(DirectObject):
    notify = directNotify.newCategory("LagCompensationAI")
    #notify.setDebug(True)

    def __init__(self):
        #self.notify.setDebug(True)
        self.playerRecords = {}

    def cleanup(self):
        self.playerRecords = None

    def registerPlayer(self, plyr):
        self.playerRecords[plyr.doId] = PlayerRecord(plyr.doId)

    def unregisterPlayer(self, plyr):
        if plyr.doId in self.playerRecords:
            del self.playerRecords[plyr.doId]

    def recordPlayerPositions(self):
        minTime = globalClock.frame_time - maxUnlag

        #self.notify.debug("Recording player positions at time " + str(globalClock.frame_time) + ", min time " + str(minTime))

        for doId, record in self.playerRecords.items():
            record.track = [x for x in record.track if x.simulationTime >= minTime]
            track = record.track

            if track and track[0].simulationTime >= globalClock.frame_time:
                continue

            plyr = base.air.doId2do.get(doId)
            if not plyr:
                continue

            #self.notify.debug("Record plyr " + str(plyr.doId) + " at pos " + str(plyr.getPos()) + ", hpr " + str(plyr.getHpr()) + ", alive " + str(not plyr.isDead()))

            sample = PlayerSample()
            sample.alive = not plyr.isDead()
            sample.simulationTime = globalClock.frame_time
            sample.pos = plyr.getPos()
            sample.hpr = plyr.getHpr()
            track.insert(0, sample)

    def startLagCompensation(self, plyr, cmd):
        correct = 0.0
        # Half RTT in seconds.
        correct += plyr.owner.averageRtt * 0.0005
        lerpTicks = base.timeToTicks(plyr.owner.interpAmount)
        correct += base.ticksToTime(lerpTicks)
        correct = max(0.0, min(maxUnlag, correct))

        targetTick = cmd.tickCount - lerpTicks
        deltaTime = correct - base.ticksToTime(base.tickCount - targetTick)

        if abs(deltaTime) > 0.2:
            targetTick = base.tickCount - base.timeToTicks(correct)

        targetTime = base.ticksToTime(targetTick)

        self.notify.debug("Start lag comp for plyr " + str(plyr.doId) + ", targetTime " + str(targetTime) + ", currentTime " + str(globalClock.frame_time))
        self.notify.debug("Half-RTT is " + str(plyr.owner.averageRtt * 0.0005) + " seconds")
        self.notify.debug("Lerp time is " + str(plyr.owner.interpAmount))
        self.notify.debug("Lerp ticks " + str(lerpTicks))
        self.notify.debug("Target tick " + str(targetTick))
        self.notify.debug("current tick " + str(base.tickCount))
        self.notify.debug("delta time " + str(deltaTime))

        #doLagCompDebug = tf_server_lag_comp_debug.value

        #positions = []

        for doId, record in self.playerRecords.items():
            if doId == plyr.doId:
                continue

            otherPlyr = base.air.doId2do.get(doId)
            if not otherPlyr:
                continue

            self.backtrackPlayer(otherPlyr, record, targetTime)

            #if doLagCompDebug:
            #    positions.append(otherPlyr.getPos())

        #if doLagCompDebug:
        #    plyr.sendUpdate('lagCompDebug', [positions])

    def finishLagCompensation(self, plyr):
        for doId, record in self.playerRecords.items():

            if not record.needsRestore:
                continue

            plyr = base.air.doId2do.get(doId)
            if not plyr:
                continue

            restore = record.restore
            change = record.change

            anyChanged = False

            if plyr.getHpr() == change.hpr:
                plyr.setHpr(restore.hpr)
                anyChanged = True

            #pdelta = plyr.getPos() - change.pos
            #if pdelta.lengthSquared() < 128.0:
            if plyr.getPos() == change.pos:
                plyr.setPos(restore.pos)
                anyChanged = True

            if anyChanged:
                plyr.invalidateHitBoxes()

            record.needsRestore = False

    def backtrackPlayer(self, plyr, record, targetTime):
        track = record.track

        if not track:
            return

        curPos = plyr.getPos()
        curHpr = plyr.getHpr()

        prevPos = Point3(plyr.getPos())
        prevSample = None
        sample = None

        for i in range(len(track)):
            prevSample = sample
            sample = track[i]

            if not sample.alive:
                return

            delta = sample.pos - prevPos
            #if delta.lengthSquared() > 128.0:
            #    return

            if sample.simulationTime <= targetTime:
                break

            prevPos = Point3(sample.pos)

        assert sample

        p = Point3()
        hpr = Vec3()

        frac = 0.0
        if prevSample and (sample.simulationTime < targetTime) and (sample.simulationTime < prevSample.simulationTime):
            assert prevSample.simulationTime > sample.simulationTime
            assert targetTime < prevSample.simulationTime

            frac = (targetTime - sample.simulationTime) / (prevSample.simulationTime - sample.simulationTime)
            assert frac > 0 and frac < 1

            p = sample.pos + (prevSample.pos - sample.pos) * frac
            hpr = sample.hpr + (prevSample.hpr - sample.hpr) * frac
        else:
            p = sample.pos
            hpr = sample.hpr

        self.notify.debug("for plyr " + str(plyr.doId) + ", p " + str(p) + ", hpr " + str(hpr))
        self.notify.debug("cur server pos " + str(curPos) + ", hpr " + str(curHpr))

        pdiff = plyr.getPos() - p
        hdiff = plyr.getHpr() - hpr

        change = record.change
        change.hpr = hpr
        change.pos = p
        restore = record.restore
        restore.hpr = plyr.getHpr()
        restore.pos = plyr.getPos()

        anyChanged = False

        if hdiff.lengthSquared() > 0.01:
            plyr.setHpr(hpr)
            anyChanged = True

        if pdiff.lengthSquared() > 0.01:
            plyr.setPos(p)
            anyChanged = True

        if anyChanged:
            plyr.invalidateHitBoxes()

        record.needsRestore = True

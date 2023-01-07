"""TriggerCaptureArea module: contains the TriggerCaptureArea class."""

from .DistributedTrigger import DistributedTrigger

from tf.tfbase import TFGlobals
from tf.player.TFClass import Class

class TriggerCaptureArea(DistributedTrigger):

    CSIdle = 0
    CSCapping = 1
    CSBlocked = 2
    CSReverting = 3

    def __init__(self):
        DistributedTrigger.__init__(self)
        self.capPoint = None
        self.capPointName = ""
        self.timeToCap = 0

        # List of team numbers that are allowed to capture this
        # control point.
        self.canCapTeams = []
        self.numRequiredToCap = []

        self.playersOnCap = []

        self.capBlocked = False

        # The team that the progress belongs to.
        self.teamProgress = TFGlobals.TFTeam.NoTeam
        self.capProgress = 0.0

        self.capState = self.CSIdle
        self.capSound = None
        self.capDoId = 0

    if not IS_CLIENT:

        def calcProgressDelta(self, team):
            timeToCap = self.timeToCap * 2 * self.numRequiredToCap[team]
            step = (1.0 / timeToCap)
            delta = step
            numPlayersOnCap = 0
            for plyr in self.playersOnCap:
                if plyr.tfClass == Class.Scout:
                    # Scouts count as 2 players.
                    numPlayersOnCap += 2
                else:
                    numPlayersOnCap += 1
            for i in range(1, numPlayersOnCap):
                delta += step / (i + 1)
            return delta * globalClock.dt

        def capUpdate(self, task):
            # If multiple teams are on the cap, progress is stagnant.
            teamOnCap = None
            for plyr in list(self.playersOnCap):
                if plyr.isDODeleted() or plyr.isDead():
                    self.playersOnCap.remove(plyr)
                    continue

                if teamOnCap is None:
                    teamOnCap = plyr.team
                elif plyr.team != teamOnCap:
                    self.capState = self.CSBlocked
                    return task.cont

            teamCanCap = (teamOnCap is not None) and (teamOnCap in self.canCapTeams)
            if teamCanCap:
                # Check that they have all the required points captured to cap
                # this point.
                prevList = self.capPoint.teamPreviousPoints.get(teamOnCap, [])
                allCapped = True
                for p in prevList:
                    if p.ownerTeam != teamOnCap:
                        allCapped = False
                        break
                if not allCapped:
                    teamCanCap = False

            # If only one team is on the cap, and that team is allowed to
            # cap, increment progress towards capture.
            if teamCanCap:

                if self.teamProgress != teamOnCap and self.capProgress > 0:
                    # Another team has progress on the capture, start reverting it.
                    # Once it's fully reverted, we can make progress towards our team
                    # capturing it.
                    self.capState = self.CSReverting
                    self.capProgress -= self.calcProgressDelta(teamOnCap)
                    self.capProgress = max(0.0, self.capProgress)

                elif self.capProgress < 1:
                    # We can start capturing it.
                    if self.capProgress == 0:
                        self.capPoint.teamStartCapping(teamOnCap)
                    self.capState = self.CSCapping
                    self.teamProgress = teamOnCap
                    self.capProgress += self.calcProgressDelta(teamOnCap)
                    self.capProgress = min(1.0, self.capProgress)
                    if self.capProgress >= 1:
                        # Capped.
                        self.capState = self.CSIdle
                        self.capPoint.capturedByTeam(self.teamProgress)
                        if self.teamProgress == TFGlobals.TFTeam.Blue:
                            self.connMgr.fireOutput("OnCapTeam2")
                        else:
                            self.connMgr.fireOutput("OnCapTeam1")

            elif self.capProgress < 1:
                # Nobody is on the cap or the team on the cap can't capture
                # (they're a defender).  Decay the progress down to 0.
                self.capState = self.CSIdle
                if self.teamProgress != TFGlobals.TFTeam.NoTeam and self.capProgress > 0:
                    timeToCap = self.timeToCap * 2 * self.numRequiredToCap[self.teamProgress]
                    step = (1.0 / (timeToCap / 90)) * globalClock.dt
                    # TODO: increase by 6 if overtime
                    self.capProgress -= step
                    self.capProgress = max(0.0, self.capProgress)
                else:
                    self.capProgress = 0

            return task.cont

        def onEntityStartTouch(self, entity):
            if not entity.isDead() and entity.isPlayer() and not entity in self.playersOnCap:
                self.playersOnCap.append(entity)

            DistributedTrigger.onEntityStartTouch(self, entity)

        def onEntityEndTouch(self, entity):
            if entity in self.playersOnCap:
                self.playersOnCap.remove(entity)

            DistributedTrigger.onEntityEndTouch(self, entity)

        def initFromLevel(self, ent, props):
            DistributedTrigger.initFromLevel(self, ent, props)
            if props.hasAttribute("area_cap_point"):
                self.capPointName = props.getAttributeValue("area_cap_point").getString()
            if props.hasAttribute("area_time_to_cap"):
                self.timeToCap = props.getAttributeValue("area_time_to_cap").getFloat()
            if props.hasAttribute("team_cancap_2") and props.getAttributeValue("team_cancap_2").getBool():
                self.canCapTeams.append(TFGlobals.TFTeam.Red)
            if props.hasAttribute("team_cancap_3") and props.getAttributeValue("team_cancap_3").getBool():
                self.canCapTeams.append(TFGlobals.TFTeam.Blue)
            if props.hasAttribute("team_numcap_2"):
                self.numRequiredToCap.append(props.getAttributeValue("team_numcap_2").getInt())
            else:
                self.numRequiredToCap.append(1)
            if props.hasAttribute("team_numcap_3"):
                self.numRequiredToCap.append(props.getAttributeValue("team_numcap_3").getInt())
            else:
                self.numRequiredToCap.append(1)

        def announceGenerate(self):
            DistributedTrigger.announceGenerate(self)
            if self.capPointName:
                self.capPoint = base.entMgr.findExactEntity(self.capPointName)
                assert self.capPoint
                self.capDoId = self.capPoint.doId
            self.addTask(self.capUpdate, 'capUpdate', appendTask=True)
    else:
        def announceGenerate(self):
            DistributedTrigger.announceGenerate(self)

            self.capPoint = base.cr.doId2do.get(self.capDoId)
            assert self.capPoint

        def disable(self):
            if self.capSound:
                self.capSound.stop()
                self.capSound = None
            self.capPoint = None
            DistributedTrigger.disable(self)

        def doCapSound(self, soundName):
            if self.capSound:
                self.capSound.stop()
                self.capSound = None
            self.capSound = self.capPoint.emitSoundSpatial(soundName)

        def RecvProxy_capState(self, state):
            self.setCapState(state)

        def setCapState(self, state):
            if state != self.capState:
                if state in (self.CSCapping, self.CSReverting):
                    self.doCapSound("Hologram.Start")
                elif state == self.CSBlocked:
                    self.doCapSound("Hologram.Interrupted")
                elif state == self.CSIdle:
                    self.doCapSound("Hologram.Stop")
                self.capState = state

if not IS_CLIENT:
    TriggerCaptureAreaAI = TriggerCaptureArea
    TriggerCaptureAreaAI.__name__ = 'TriggerCaptureAreaAI'

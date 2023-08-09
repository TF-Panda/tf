"""TriggerCaptureAreaAI module: contains the TriggerCaptureAreaAI class."""

from tf.player.TFClass import Class
from tf.tfbase import TFGlobals

from . import CapState
from .DistributedTrigger import DistributedTriggerAI


class TriggerCaptureAreaAI(DistributedTriggerAI):

    """
    AI capture area implementation.
    """

    def __init__(self):
        DistributedTriggerAI.__init__(self)

        self.capPointName = ""
        self.capPoint = None
        self.timeToCap = 0

        # List of team numbers that are allowed to capture this
        # control point.
        self.canCapTeams = []
        self.numRequiredToCap = []

        self.playersOnCap = []
        self.capperCount = 0

        self.capBlocked = False

        # The team that the progress belongs to.
        self.teamProgress = TFGlobals.TFTeam.NoTeam
        self.capProgress = 0.0

        self.capState = CapState.CSIdle
        self.capDoId = 0

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
        self.setCapperCount(numPlayersOnCap)
        for i in range(1, numPlayersOnCap):
            delta += step / (i + 1)
        return delta * base.clockMgr.getDeltaTime()

    def canTeamCap(self, team):
        ret = (team is not None) and (team in self.canCapTeams) and (base.game.controlPointMaster.canTeamWin(team))
        if ret:
            # Check that they have all the required points captured to cap
            # this point.
            prevList = self.capPoint.teamPreviousPoints.get(team, [])
            allCapped = True
            for p in prevList:
                if p.ownerTeam != team:
                    allCapped = False
                    break
            if not allCapped:
                ret = False
        return ret

    def getTeamsOnCap(self):
        teams = set()
        for p in self.playersOnCap:
            teams.add(p.team)
        return teams

    def pointCanBeCapped(self):
        if base.game.isRoundEnded():
            return False

        for team in range(TFGlobals.TFTeam.COUNT):
            canCap = self.canTeamCap(team)
            if canCap and self.capPoint.ownerTeam != team:
                return True
        return False

    def handleBlocked(self):
        # Find the team that defended the point.

        if self.capPoint.ownerTeam == TFGlobals.TFTeam.NoTeam:
            # This is just a contested point.
            return

        # Otherwise, any players on the point, on the team that
        # owns the point, defended it.
        defenders = []
        for p in self.playersOnCap:
            if p.team == self.capPoint.ownerTeam:
                defenders.append(p)

        if defenders:
            base.game.sendUpdate('defendedPointEvent', [defenders[0].doId, self.capPoint.pointName])

    def capUpdate(self, task):
        if base.game.isRoundEnded():
            self.setCapProgress(0)
            return task.cont

        self.setCapperCount(0)

        self.playersOnCap = [x for x in self.playersOnCap if not x.isDODeleted() and not x.isDead()]

        # If multiple teams are on the cap, progress is stagnant.
        teamOnCap = None
        for plyr in self.playersOnCap:
            if teamOnCap is None:
                teamOnCap = plyr.team
            elif plyr.team != teamOnCap and self.pointCanBeCapped():
                if self.capState != CapState.CSBlocked:
                    self.handleBlocked()
                self.setCapState(CapState.CSBlocked)
                return task.cont

        # If only one team is on the cap, and that team is allowed to
        # cap, increment progress towards capture.
        if self.canTeamCap(teamOnCap):

            if self.teamProgress != teamOnCap and self.capProgress > 0:
                # Another team has progress on the capture, start reverting it.
                # Once it's fully reverted, we can make progress towards our team
                # capturing it.
                self.setCapState(CapState.CSReverting)
                prog = self.capProgress - self.calcProgressDelta(teamOnCap)
                prog = max(0.0, prog)
                self.setCapProgress(prog)

            elif self.capProgress < 1:
                # We can start capturing it.
                if self.capProgress == 0:
                    self.capPoint.teamStartCapping(teamOnCap)
                self.setCapState(CapState.CSCapping)
                self.teamProgress = teamOnCap
                prog = self.capProgress
                prog += self.calcProgressDelta(teamOnCap)
                prog = min(1.0, prog)
                self.setCapProgress(prog)
                if prog >= 1:
                    # Capped.
                    self.setCapState(CapState.CSIdle)
                    self.capPoint.capturedByTeam(self.teamProgress)
                    if self.teamProgress == TFGlobals.TFTeam.Blue:
                        self.connMgr.fireOutput("OnCapTeam2")
                    else:
                        self.connMgr.fireOutput("OnCapTeam1")
                    for p in self.playersOnCap:
                        p.speakConcept(TFGlobals.SpeechConcept.CappedObjective, {'gamemode': 'cp'})
                    base.game.sendUpdate('cappedPointEvent', [self.playersOnCap[0].doId, self.capPoint.pointName])

        elif self.capProgress < 1:
            # Nobody is on the cap or the team on the cap can't capture
            # (they're a defender).  Decay the progress down to 0.
            self.setCapState(CapState.CSIdle)
            if self.teamProgress != TFGlobals.TFTeam.NoTeam and self.capProgress > 0:
                decayFactor = 1.5
                if base.game.inOverTime:
                    decayFactor *= 3.0
                decrease = self.timeToCap * 2 * self.numRequiredToCap[self.teamProgress]
                decrease /= decayFactor
                prog = self.capProgress
                prog -= (1.0 / decrease) * base.clockMgr.getDeltaTime()
                prog = max(0.0, prog)
                self.setCapProgress(prog)
            else:
                self.setCapProgress(0)

        return task.cont

    def onEntityStartTouch(self, entity):
        if not entity.isDead() and entity.isPlayer() and not entity in self.playersOnCap:
            self.playersOnCap.append(entity)

        DistributedTriggerAI.onEntityStartTouch(self, entity)

    def onEntityEndTouch(self, entity):
        if entity in self.playersOnCap:
            self.playersOnCap.remove(entity)

        DistributedTriggerAI.onEntityEndTouch(self, entity)

    def initFromLevel(self, ent, props):
        DistributedTriggerAI.initFromLevel(self, ent, props)
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
        DistributedTriggerAI.announceGenerate(self)
        if self.capPointName:
            self.capPoint = base.entMgr.findExactEntity(self.capPointName)
            assert self.capPoint
            self.capDoId = self.capPoint.doId
        self.addTask(self.capUpdate, 'capUpdate', appendTask=True)

    def setCapState(self, state):
        self.capState = state
        self.capPoint.capState = state

    def setCapProgress(self, prog):
        self.capProgress = prog
        self.capPoint.capProgress = prog

    def setCapperCount(self, count):
        self.capperCount = count
        self.capPoint.capperCount = count

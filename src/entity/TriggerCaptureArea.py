"""TriggerCaptureArea module: contains the TriggerCaptureArea class."""

from .DistributedTrigger import DistributedTrigger

from tf.tfbase import TFGlobals

class TriggerCaptureArea(DistributedTrigger):

    def __init__(self):
        DistributedTrigger.__init__(self)
        self.capPoint = None
        self.capPointName = ""
        self.timeToCap = 0

        # List of team numbers that are allowed to capture this
        # control point.
        self.canCapTeams = []

        self.playersOnCap = []

        self.capBlocked = False

        # The team that the progress belongs to.
        self.teamProgress = TFGlobals.TFTeam.NoTeam
        self.capProgress = 0

        self.ownedTeam = 2

    if not IS_CLIENT:
        def capUpdate(self, task):
            # If multiple teams are on the cap, progress is stagnant.
            teamOnCap = None
            for plyr in self.playersOnCap:
                if teamOnCap is None:
                    teamOnCap = plyr.team
                elif plyr.team != teamOnCap:
                    print("cap stalemate")
                    return task.cont

            # If only one team is on the cap, and that team is allowed to
            # cap, increment progress towards capture.
            if teamOnCap is not None and teamOnCap in self.canCapTeams:
                if self.teamProgress != teamOnCap and self.capProgress > 0:
                    # Another team has progress on the capture, start reverting it.
                    # Once it's fully reverted, we can make progress towards our team
                    # capturing it.
                    self.capProgress -= (1.0 / self.timeToCap) * globalClock.dt
                    self.capProgress = max(0.0, self.capProgress)
                    if self.capProgress > 0:
                        print("revert cap", self.teamProgress, self.capProgress)
                else:
                    # We can start capturing it.
                    self.teamProgress = teamOnCap
                    self.capProgress += (1.0 / self.timeToCap) * globalClock.dt
                    self.capProgress = min(1.0, self.capProgress)
                    if self.capProgress < 1:
                        print("inc cap", self.teamProgress, self.capProgress)
            else:
                # Nobody is on the cap or the team on the cap can't capture
                # (they're a defender).  Decay the progress down to 0.
                self.capProgress -= (1.0 / self.timeToCap) * globalClock.dt
                self.capProgress = max(0.0, self.capProgress)
                if self.capProgress > 0:
                    print("decay cap", self.capProgress)

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

        def announceGenerate(self):
            DistributedTrigger.announceGenerate(self)
            if self.capPointName:
                self.capPoint = base.entMgr.findExactEntity(self.capPointName)
                #assert self.capPoint
            self.addTask(self.capUpdate, 'capUpdate', appendTask=True)

if not IS_CLIENT:
    TriggerCaptureAreaAI = TriggerCaptureArea
    TriggerCaptureAreaAI.__name__ = 'TriggerCaptureAreaAI'

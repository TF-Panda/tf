"""TeamRoundTimerAI module: contains the TeamRoundTimerAI class."""

from direct.distributed2.DistributedObjectAI import DistributedObjectAI

from .EntityBase import EntityBase
from tf.tfbase import TFGlobals

import random, math

class TeamRoundTimerAI(DistributedObjectAI, EntityBase):

    def __init__(self):
        DistributedObjectAI.__init__(self)
        EntityBase.__init__(self)
        self.timeLeft = 0.0
        self.timeLeftInteger = 0
        self.timerLength = 0.0
        self.setupLength = 0.0
        self.startPaused = False
        self.autoCountdown = True
        self.running = False
        self.team = TFGlobals.TFTeam.NoTeam
        self.enabled = True

        self.timerIsSetup = False

    def stopTimer(self):
        self.removeTask('timerUpdate')
        self.enabled = False
        self.running = False

    def isNetworkedEntity(self):
        return True

    def input_Pause(self, caller):
        self.removeTask('timerUpdate')

    def input_Resume(self, caller):
        if self.running:
            self.addTask(self.__timerUpdate, 'timerUpdate', appendTask=True)

    def input_SetTime(self, caller, time):
        self.timeLeft = float(time)

    def input_AddTime(self, caller, time):
        self.timeLeft += float(time)
        base.world.emitSound("Announcer.TimeAdded")

    def input_AddTeamTime(self, caller, data):
        data = data.split()
        rewardedTeam = int(data[0]) - 2
        time = float(data[1])
        self.timeLeft += time

        if rewardedTeam != TFGlobals.TFTeam.NoTeam:
            if random.random() < 0.25:
                base.game.teamSound("Announcer.TimeAdded", rewardedTeam)
            else:
                base.game.teamSound("Announcer.TimeAwardedForTeam", rewardedTeam)
            base.game.enemySound("Announcer.TimeAddedForEnemy", rewardedTeam)
        else:
            base.world.emitSound("Announcer.TimeAdded")

    def startSetupTimer(self):
        self.timeLeft = self.setupLength
        self.timerIsSetup = True
        if self.startPaused:
            self.paused = True
        else:
            self.addTask(self.__timerUpdate, 'timerUpdate', appendTask=True)
        self.connMgr.fireOutput("OnSetupStart")
        self.running = True
        self.enabled = True

    def startTimer(self):
        self.timeLeft = self.timerLength
        self.timerIsSetup = False
        if self.startPaused:
            self.paused = True
        else:
            self.addTask(self.__timerUpdate, 'timerUpdate', appendTask=True)
        self.connMgr.fireOutput("OnRoundStart")
        self.running = True
        self.enabled = True

    def __timerUpdate(self, task):
        prevTime = self.timeLeft
        self.timeLeft -= globalClock.dt
        self.timeLeft = max(0.0, self.timeLeft)
        self.timeLeftInteger = math.ceil(self.timeLeft)

        if self.timeLeft <= 0:
            if self.timerIsSetup:
                self.connMgr.fireOutput("OnSetupFinished")
                # Start the normal round timer.
                base.game.beginRound()
                self.startTimer()
            else:
                self.connMgr.fireOutput("OnFinished")
            return task.done

        time = self.timeLeft

        if prevTime > 1 and time <= 1:
            self.connMgr.fireOutput("On1SecRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins1Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds1seconds")

        elif prevTime > 2 and time <= 2:
            self.connMgr.fireOutput("On2SecRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins2Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds2seconds")

        elif prevTime > 3 and time <= 3:
            self.connMgr.fireOutput("On3SecRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins3Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds3seconds")

        elif prevTime > 4 and time <= 4:
            self.connMgr.fireOutput("On4SecRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 4 seconds.
                    base.world.emitSound("Announcer.RoundBegins4Seconds")
                else:
                    # Mission ends in 4 seconds.
                    base.world.emitSound("Announcer.RoundEnds4seconds")

        elif prevTime > 5 and time <= 5:
            self.connMgr.fireOutput("On5SecRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 5 seconds.
                    base.world.emitSound("Announcer.RoundBegins5Seconds")
                else:
                    # Mission ends in 5 seconds.
                    base.world.emitSound("Announcer.RoundEnds5seconds")

        elif prevTime > 10 and time <= 10:
            self.connMgr.fireOutput("On10SecRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 10 seconds.
                    base.world.emitSound("Announcer.RoundBegins10Seconds")
                else:
                    # Mission ends in 10 seconds.
                    base.world.emitSound("Announcer.RoundEnds10seconds")

        elif prevTime > 30 and time <= 30:
            self.connMgr.fireOutput("On30SecRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 30 seconds.
                    base.world.emitSound("Announcer.RoundBegins30Seconds")
                else:
                    # Mission ends in 30 seconds.
                    base.world.emitSound("Announcer.RoundEnds30seconds")

        elif prevTime > 60 and time <= 60:
            self.connMgr.fireOutput("On1MinRemain")
            if self.autoCountdown:
                if self.timerIsSetup:
                    # Mission begins in 60 seconds.
                    base.world.emitSound("Announcer.RoundBegins60Seconds")
                else:
                    # Mission ends in 60 seconds.
                    base.world.emitSound("Announcer.RoundEnds60seconds")

        elif prevTime > 300 and time <= 300:
            self.connMgr.fireOutput("On5MinRemain")
            # Mission ends in 5 minutes.
            if not self.timerIsSetup and self.autoCountdown:
                base.world.emitSound("Announcer.RoundEnds5minutes")

        return task.cont

    def initFromLevel(self, ent, props):
        EntityBase.initFromLevel(self, ent, props)
        if props.hasAttribute("TeamNum"):
            self.team = props.getAttributeValue("TeamNum").getInt() - 2
        if props.hasAttribute("start_paused"):
            self.startPaused = props.getAttributeValue("start_paused").getBool()
        if props.hasAttribute("setup_length"):
            self.setupLength = props.getAttributeValue("setup_length").getFloat()
        if props.hasAttribute("timer_length"):
            self.timerLength = props.getAttributeValue("timer_length").getFloat()
        if props.hasAttribute("auto_countdown"):
            self.autoCountdown = props.getAttributeValue("auto_countdown").getBool()

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        base.game.roundTimer = self

    def delete(self):
        EntityBase.delete(self)
        DistributedObjectAI.delete(self)
        base.game.roundTimer = None


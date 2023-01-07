"""TeamRoundTimer module: contains the TeamRoundTimer class."""

from direct.distributed2.DistributedObject import DistributedObject

from tf.tfbase import TFGlobals, TFLocalizer

from direct.gui.DirectGui import OnscreenText, DGG

class TeamRoundTimer(DistributedObject):

    def __init__(self):
        DistributedObject.__init__(self)
        self.timeLeftInteger = 0
        self.timerIsSetup = False
        self.inOverTime = False
        self.team = TFGlobals.TFTeam.NoTeam
        self.enabled = False

        self.textLbl = None
        self.lastRoundTimeText = ""

    def generate(self):
        DistributedObject.generate(self)
        self.textLbl = OnscreenText(
          fg=(0.984, 0.925, 0.796, 1.0), shadow=(0, 0, 0, 1),
          parent=base.a2dTopCenter, pos=(0, -0.15), scale=0.08)
        if self.team == TFGlobals.TFTeam.Red:
            self.textLbl['bg'] = (0.9, 0.5, 0.5, 0.75)
        else:
            self.textLbl['bg'] = (0.5, 0.65, 1, 0.75)

    def postDataUpdate(self):
        DistributedObject.postDataUpdate(self)
        if self.enabled:
            self.textLbl.show()
            self.updateTimerText()
        else:
            self.textLbl.hide()

    def updateTimerText(self):
        if self.inOverTime:
            text = TFLocalizer.TimerOverTime
        else:
            minutes = self.timeLeftInteger // 60
            seconds = self.timeLeftInteger % 60

            if self.timerIsSetup:
                text = TFLocalizer.TimerSetup + "\n"
            else:
                text = ""
            text += str(minutes) + ":" + str(seconds).zfill(2)

        if text != self.lastRoundTimeText:
            self.textLbl['text'] = text
            self.lastRoundTimeText = text

    def delete(self):
        if self.textLbl:
            self.textLbl.destroy()
            self.textLbl = None
        DistributedObject.delete(self)



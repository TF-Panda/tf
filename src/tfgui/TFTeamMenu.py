"""TFTeamMenu module: contains the TFTeamMenu class."""

from panda3d.core import *

from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject

from tf.tfbase import TFLocalizer, TFGlobals
from tf.tfbase.TFGlobals import TFTeam

class TFTeamMenu(DirectObject):

    def __init__(self):
        self.frame = DirectFrame(
          frameSize = (-0.85, 0.85, -0.65, 0.65), relief = DGG.FLAT,
          frameColor = (0, 0, 0, 0.75))
        self.frame.setBin('fixed', 0)

        self.titleLbl = OnscreenText(parent = self.frame, text = "Choose a Team", font = TFGlobals.getTF2SecondaryFont(),
                                     scale = 0.1, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1), pos = (0, 0.55))
        self.titleLbl.setBin('fixed', 2)

        self.teamButtons = []
        z = 0.3
        teamNames = {
          TFTeam.Red: TFLocalizer.RED,
          TFTeam.Blue: TFLocalizer.BLU
        }
        for team in range(TFTeam.COUNT):
            name = teamNames[team]

            btn = DirectButton(relief = None, text = name,
                               text_font = TFGlobals.getTF2SecondaryFont(),
                               text_scale = 0.08,
                               parent = self.frame, text_align = TextNode.ACenter,
                               text_shadow = (0, 0, 0, 1),
                               pos = (0, 0, z), text0_fg = (1, 1, 1, 1), text1_fg = (0.75, 0.75, 0.75, 1),
                               text2_fg = (0.75, 0.75, 0.75, 1), pressEffect = False,
                               command = self.pickTeam, extraArgs = [team])
            btn.setBin('fixed', 2)
            z -= 0.1
            btn.teamId = team
            self.teamButtons.append(btn)

    def pickTeam(self, team):
        base.localAvatar.d_changeTeam(team)
        self.destroy()

    def destroy(self):
        for btn in self.teamButtons:
            btn.destroy()
        del self.teamButtons
        self.frame.destroy()
        del self.frame

"""WinPanel module: contains the WinPanel class."""

from direct.gui.DirectGui import *
from tf.tfbase import TFLocalizer, TFGlobals
from . import TFGuiProperties

class WinPanel:

    def __init__(self, winTeam, winReason):
        if winTeam == TFGlobals.TFTeam.Red:
            frameColor = TFGuiProperties.BackgroundColorRedTranslucent
            teamName = TFLocalizer.RED

        elif winTeam == TFGlobals.TFTeam.Blue:
            frameColor = TFGuiProperties.BackgroundColorBlueTranslucent
            teamName = TFLocalizer.BLU

        else:
            frameColor = TFGuiProperties.BackgroundColorNeutralTranslucent

        if winReason == TFGlobals.WinReason.SeizedArea:
            headingText = TFLocalizer.WinPanelHeadingSeizesArea % teamName

        elif winReason == TFGlobals.WinReason.Stalemate or winTeam == TFGlobals.TFTeam.NoTeam:
            headingText = TFLocalizer.WinPanelHeadingStalemate

        else:
            headingText = TFLocalizer.WinPanelHeadingTeamWins % teamName

        if winReason in (TFGlobals.WinReason.SeizedArea, TFGlobals.WinReason.CapturedPoints):
            reasonText = TFLocalizer.WinPanelReasonCaptured % teamName

        elif winReason == TFGlobals.WinReason.Defended:
            reasonText = TFLocalizer.WinPanelReasonDefended % teamName

        elif winReason == TFGlobals.WinReason.Stalemate:
            reasonText = TFLocalizer.WinPanelReasonStalemate
        else:
            reasonText = ""

        self.frame = DirectFrame(frameColor=frameColor, relief=DGG.FLAT, frameSize=(-0.6, 0.6, -0.3, 0.1), pos=(0, 0, -0.15))

        self.headingLbl = DirectLabel(parent=self.frame, text=headingText, text_font=TFGlobals.getTF2Font(), text_scale=0.1, relief=None,
                                      text_fg=TFGuiProperties.TextColorLight, text_shadow=TFGuiProperties.TextShadowColor)
        self.reasonLbl = DirectLabel(parent=self.frame, text=reasonText, text_font=TFGlobals.getTF2SecondaryFont(), text_scale=0.06, relief=None,
                                     text_fg=TFGuiProperties.TextColorLight, text_shadow=TFGuiProperties.TextShadowColor, pos=(0, 0, -0.15),
                                     text_wordwrap=20)

    def cleanup(self):
        self.headingLbl.destroy()
        self.headingLbl = None
        self.reasonLbl.destroy()
        self.reasonLbl = None
        self.frame.destroy()
        self.frame = None

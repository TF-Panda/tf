"""TFDialog module: contains the TFDialog class."""

from direct.gui.DirectGui import *
from direct.directnotify.DirectNotifyGlobal import directNotify
from tf.tfbase import TFLocalizer, TFGlobals
from tf.tfgui import TFGuiProperties

class TFDialog(DirectDialog):
    notify = directNotify.newCategory('TFDialog')

    NoButtons = 0
    Acknowledge = 1
    CancelOnly = 2
    OkCancel = 3
    YesNo = 4

    def __init__(self, parent=None, style=NoButtons, **kw):

        if not parent:
            parent = base.aspect2d

        self.style = style

        if style == TFDialog.Acknowledge:
            buttonText = [TFLocalizer.OK]
            buttonValue = [DGG.DIALOG_OK]
        elif style == TFDialog.CancelOnly:
            buttonText = [TFLocalizer.Cancel]
            buttonValue = [DGG.DIALOG_CANCEL]
        elif style == TFDialog.OkCancel:
            buttonText = [TFLocalizer.OK, TFLocalizer.Cancel]
            buttonValue = [DGG.DIALOG_OK, DGG.DIALOG_CANCEL]
        elif style == TFDialog.YesNo:
            buttonText = [TFLocalizer.Yes, TFLocalizer.No]
            buttonValue = [DGG.DIALOG_YES, DGG.DIALOG_NO]
        elif style == TFDialog.NoButtons:
            buttonText = []
            buttonValue = []
        else:
            self.notify.error("Unknown TFDialog style: " + str(style))

        font = TFGlobals.getTF2SecondaryFont()
        optiondefs = (
            ('buttonTextList', buttonText, DGG.INITOPT),
            ('buttonValueList', buttonValue, DGG.INITOPT),
            ('buttonPadSF', 2.2, DGG.INITOPT),
            ('text_font', font, None),
            ('button_text_font', font, None),
            ('text_fg', TFGuiProperties.TextColorLight, None),
            ('text_shadow', TFGuiProperties.TextShadowColor, None),
            ('button_text_fg', TFGuiProperties.TextColorLight, None),
            ('button_text_shadow', TFGuiProperties.TextShadowColor, None),
            ('relief', DGG.FLAT, None),
            ('button_relief', DGG.FLAT, None),
            ('frameColor', TFGuiProperties.BackgroundColorNeutralTranslucent, None),
            ('button_frameColor', (TFGuiProperties.BackgroundColorNeutralTranslucent, (0.61, 0.32, 0.13, 1)), None),
            ('fadeScreen', 0.5, None),
            ('text_wordwrap', 18, None),
            ('button_pad', (0.01, 0.01), None),
            ('text_scale', 0.07, None),
        )

        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(TFDialog)

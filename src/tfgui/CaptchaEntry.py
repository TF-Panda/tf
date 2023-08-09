"""CaptchaEntry module: contains the CaptchaEntry class."""

from panda3d.core import PNMImage, StringStream, TextNode, Texture

from direct.fsm.FSM import FSM
from direct.gui.DirectGui import DirectEntry, OnscreenImage, OnscreenText
from tf.tfbase import TFGlobals
from tf.tfgui import TFGuiProperties
from tf.tfgui.TFDialog import TFDialog


class CaptchaEntry(FSM):

    def __init__(self, imageData):
        FSM.__init__(self, "CaptchaEntry")
        img = PNMImage()
        img.read(StringStream(imageData))
        self.captchaTex = Texture('captcha')
        self.captchaTex.load(img)
        self.captchaTex.setFormat(Texture.FSrgb)
        self.triesLeft = 0

    def enterValidating(self):
        dlg = TFDialog(style=TFDialog.NoButtons, text="Validating...")
        dlg.show()
        self.dlg = dlg

    def exitValidating(self):
        self.dlg.cleanup()
        del self.dlg

    def enterPrompt(self):
        sizeX = self.captchaTex.getXSize()
        sizeY = self.captchaTex.getYSize()
        displayWidth = 0.3
        scaleX = displayWidth
        scaleY = (sizeY / sizeX) * displayWidth
        dlg = TFDialog(style=TFDialog.Acknowledge, text="Please enter the text in the image below.", midPad=0.5,
                       topPad=0.0, pad=(0.1, 0.1), text_align=TextNode.ACenter, text_wordwrap=20,
                       pos=(0, 0, 0.3), command=self.__promptAck)
        oimg = OnscreenImage(self.captchaTex, parent=dlg, scale=(scaleX, 1, scaleY), pos=(0, 0, -0.2))
        entry = DirectEntry(parent=dlg, pos=(-0.08 * 5, 0, -0.45), scale=0.08,
                            frameColor=TFGuiProperties.BackgroundColorNeutralTranslucent,
                            text_fg=TFGuiProperties.TextColorLight,
                            text_shadow=TFGuiProperties.TextShadowColor,
                            entryFont=TFGlobals.getTF2SecondaryFont(), command=self.__promptAck)
        dlg.show()

        self.dlg = dlg
        self.oimg = oimg
        self.entry = entry

        if self.triesLeft > 0:
            self.badLbl = OnscreenText(parent=dlg, pos=(0, -0.585),
                                       text="Try again.  %i tries remaining." % self.triesLeft,
                                       font=TFGlobals.getTF2SecondaryFont(),
                                       fg=TFGuiProperties.TextColorRed, shadow=TFGuiProperties.TextShadowColor)

    def __promptAck(self, _):
        messenger.send('CaptchaPromptAck', [self.entry.get().strip()])

    def exitPrompt(self):
        self.oimg.destroy()
        del self.oimg
        self.entry.destroy()
        del self.entry
        self.dlg.cleanup()
        del self.dlg
        if hasattr(self, 'badLbl'):
            self.badLbl.destroy()
            del self.badLbl

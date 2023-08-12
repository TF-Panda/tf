"""ChatFeed module: contains the ChatFeed class."""

from panda3d.core import *

from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject

from .TextBuffer import TextBuffer


class ChatFeed(DirectObject):

    # The maximum number of chat labels we can have in the feed at a given time.
    MaxChats = 8
    ChatWindowSizeX = 1.5
    ChatWindowSizeY = 0.466
    ChatVPad = 0.01
    ChatWordwrap = 25
    ChatScale = 0.04
    ChatLifetime = 10.0
    MaxWindowSizeZ = 0.5
    ChatColor = (0.984, 0.925, 0.796, 1.0)

    # Amount of time we show the chat feed after activity.
    PeekInterval = 10.0

    def __init__(self):
        self.chatSound = base.loader.loadSfx("sound/ui/chat_display_text.wav")
        self.chatSound.setVolume(0.5)

        self.teamOnlyChat = False

        self.root = NodePath("chatRoot")
        self.root.reparentTo(base.a2dBottomLeft)
        self.root.setPos(0.1, 0, 1.0)

        bufferDim = (0, 1, -0.4, 0)

        font = loader.loadFont("models/fonts/arial.ttf")#TFGlobals.getTF2SecondaryFont()
        self.buffer = TextBuffer(dimensions=bufferDim, enterCallback=self.onEnterChat, font=font, parent=self.root, textColor=self.ChatColor, width=30)

        self.accept('window-event', self.winEvent)
        self.lastWinSize = LPoint2i(base.win.getXSize(), base.win.getYSize())
        self.adjustTextSizeForWindow(self.lastWinSize)

    def winEvent(self, win):
        if win != base.win:
            return

        newSize = LPoint2i(base.win.getXSize(), base.win.getYSize())
        if newSize != self.lastWinSize:
            self.adjustTextSizeForWindow(newSize)
            self.lastWinSize = newSize

    def adjustTextSizeForWindow(self, size):
        factor = max((size.y / 36), 10)
        self.buffer.adjustTextWidth(factor)

    def hideChatEntry(self):
        self.buffer.close()

    def showChatEntry(self, teamOnly):
        if self.buffer.isOpen:
            return

        self.teamOnlyChat = teamOnly

        if hasattr(base, 'localAvatar'):
            base.localAvatar.disableControls()

        self.buffer.open()

    def onEnterChat(self, text):
        # Don't send empty chats.  Server also checks this.
        if text:
            if hasattr(base, 'localAvatar'):
                if text[0] == '~' and base.cr.magicWordManager:
                    # It's a magic word, don't actually say it.
                    response = base.cr.magicWordManager.b_setMagicWord(text)
                    if response:
                        self.addChat("Magic words: " + response)
                else:
                    # Send to server so it can relay the chat to other clients.
                    base.localAvatar.sendUpdate('say', [text, self.teamOnlyChat])
                    # Display on our end immediately.
                    base.localAvatar.playerChat(text, self.teamOnlyChat)
            else:
                self.addChat(text)
        if hasattr(base, 'localAvatar'):
            base.localAvatar.enableControls()
        self.hideChatEntry()

    def cleanup(self):
        self.buffer.cleanup()
        self.buffer = None

    def addChat(self, text, playSound=True):

        def lblFade(val, lbl):
            lbl.setColorScale(1, 1, 1, max(val, self.buffer.alpha), 1)

        def finishLblFade(lbl):
            lbl.clearColorScale()
            lbl.show()

        label = self.buffer.addLine(text)
        label.label.setColorScale(1, 1, 1, 0, 1)
        label.label.showThrough()
        # Setup fade track.
        track = Sequence(
            LerpFunc(lblFade, fromData=0, toData=1, duration=0.3, extraArgs=[label.label]),
            Wait(self.ChatLifetime - 0.6),
            LerpFunc(lblFade, fromData=1, toData=0, duration=0.3, extraArgs=[label.label]),
            Func(finishLblFade, label.label)
        )
        track.start()
        label.track = track

        if playSound:
            self.chatSound.play()

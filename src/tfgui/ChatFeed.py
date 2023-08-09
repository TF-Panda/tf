"""ChatFeed module: contains the ChatFeed class."""

from panda3d.core import *

from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from tf.tfbase import TFGlobals

from .TextBuffer import TextBuffer


class Chat:

    def __init__(self, lbl, lifetime, size):
        self.lbl = lbl
        self.lifetime = lifetime
        self.removeTime = globalClock.frame_time + self.lifetime
        self.size = size
        self.track = Sequence(
            LerpColorScaleInterval(self.lbl, 0.3, (1, 1, 1, 1), (1, 1, 1, 0)),
            Wait(self.lifetime - 0.6),
            LerpColorScaleInterval(self.lbl, 0.3, (1, 1, 1, 0), (1, 1, 1, 1))
        )
        self.track.start()

    def cleanup(self):
        self.lbl.destroy()
        self.lbl = None
        self.track.finish()
        self.track = None

class ChatFeed:

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

        self.task = base.taskMgr.add(self.__updateTask, 'chatFeedUpdate')

        self.teamOnlyChat = False

        self.hideTime = 0.0

        self.root = NodePath("chatRoot")
        self.root.reparentTo(base.a2dBottomLeft)
        self.root.setPos(0.1, 0, 1.0)

        bufferDim = (0, 1, -0.5, 0)

        self.buffer = TextBuffer(dimensions=bufferDim, enterCallback=self.onEnterChat, font=TFGlobals.getTF2SecondaryFont(), parent=self.root)

        # Hide the buffer window and all that but keep the text.
        self.canvasInstanceRoot = self.root.attachNewNode("canvasInstance")
        self.canvasInstanceRoot.setTransparency(True)
        self.canvasInstance = self.buffer.scrollFrame.getCanvas().instanceTo(self.canvasInstanceRoot)

        self.alpha = 0.0
        self.goalAlpha = 0.0
        self.fadeOutSpeed = 4.0
        self.fadeInSpeed = 4.0

    def showPeek(self):
        self.goalAlpha = 1.0
        self.canvasInstanceRoot.unstash()

    def hidePeek(self):
        self.goalAlpha = 0.0

    def hideChatEntry(self):
        self.buffer.close()
        if self.hideTime > globalClock.frame_time:
            self.showPeek()

    def showChatEntry(self, teamOnly):
        if self.buffer.isOpen:
            return

        self.teamOnlyChat = teamOnly

        if hasattr(base, 'localAvatar'):
            base.localAvatar.disableControls()

        self.buffer.open()
        self.hidePeek()

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

    def update(self):
        if self.hideTime <= globalClock.frame_time:
            self.hidePeek()

        if self.alpha != self.goalAlpha:
            if self.alpha > self.goalAlpha:
                # Fade out.
                self.alpha = TFGlobals.approach(self.goalAlpha, self.alpha, self.fadeOutSpeed * globalClock.dt)
                if self.alpha == self.goalAlpha:
                    self.canvasInstanceRoot.stash()
            else:
                # Fade in.
                self.alpha = TFGlobals.approach(self.goalAlpha, self.alpha, self.fadeInSpeed * globalClock.dt)

            self.canvasInstanceRoot.setColorScale(1, 1, 1, self.alpha)

    def __updateTask(self, task):
        self.update()
        return task.cont

    def addChat(self, text, playSound=True):
        self.buffer.addLine(text)
        if playSound:
            self.chatSound.play()
        if not self.buffer.isOpen:
            self.showPeek()
        self.hideTime = globalClock.frame_time + self.PeekInterval

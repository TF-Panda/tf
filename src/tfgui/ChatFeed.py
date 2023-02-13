"""ChatFeed module: contains the ChatFeed class."""

from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *

from tf.tfbase import TFGlobals
from tf.tfgui import TFGuiProperties

from panda3d.core import *

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

    def __init__(self):
        self.root = base.a2dBottomLeft.attachNewNode("chatFeedRoot")
        self.root.setPos(0.1, 0, 0.4)
        self.chatRoot = self.root.attachNewNode("chatRoot")
        self.chatRoot.setEffect(
            ScissorEffect.makeNode((0, 0, 0), (0, 0, self.ChatWindowSizeY),
                                  (self.ChatWindowSizeX, 0, self.ChatWindowSizeY),
                                  (self.ChatWindowSizeX, 0, 0), self.root))
        self.chats = []

        self.chatSound = base.loader.loadSfx("sound/ui/chat_display_text.wav")
        self.chatSound.setVolume(0.5)

        self.task = base.taskMgr.add(self.__updateTask, 'chatFeedUpdate')

        self.chatEntry = None
        self.suppressFrame = None
        self.teamOnlyChat = False

    def hideChatEntry(self):
        #if self.suppressFrame:
        #    self.suppressFrame.destroy()
        #    self.suppressFrame = None
        if self.chatEntry:
            self.chatEntry.destroy()
            self.chatEntry = None

    def showChatEntry(self, teamOnly):
        if self.chatEntry:
            return

        self.teamOnlyChat = teamOnly

        base.localAvatar.disableControls()

        #self.suppressFrame = DirectFrame(frameSize=(-1000, 1000, -1000, 1000), parent=self.root, relief=DGG.FLAT, suppressKeys=True, suppressMouse=True,
        #                                 frameColor=(0.5, 0.5, 0.5, 0.5))
        #self.suppressFrame.guiItem.setFocus(1)
        #self.suppressFrame.guiItem.setBackgroundFocus(1)
        #print(self.suppressFrame.guiItem.getFrame())
        self.chatEntry = DirectEntry(overflow=0, parent=self.root, scale=self.ChatScale, pos=(0, 0, -0.05), width=25,
                                     frameColor=TFGuiProperties.BackgroundColorNeutralTranslucent, text_fg=self.ChatColor, text_shadow=(0, 0, 0, 1), focus=1,
                                     command=self.onEnterChat, entryFont=TFGlobals.getTF2SecondaryFont(), suppressKeys=1, suppressMouse=1)

    def onEnterChat(self, text):
        # Don't send empty chats.  Server also checks this.
        if text:
            # Send to server so it can relay the chat to other clients.
            base.localAvatar.sendUpdate('say', [text, self.teamOnlyChat])
            # Display on our end immediately.
            base.localAvatar.playerChat(text, self.teamOnlyChat)
        base.localAvatar.enableControls()
        self.hideChatEntry()

    def cleanup(self):
        for chat in self.chats:
            chat.cleanup()
        self.chats = None
        self.chatRoot.removeNode()
        self.chatRoot = None
        self.root.removeNode()
        self.root = None
        self.task.remove()
        self.task = None

    def removeChat(self, info):
        info.cleanup()
        self.chats.remove(info)

    def update(self):
        removeChats = []
        for chat in self.chats:
            if globalClock.frame_time >= chat.removeTime:
                removeChats.append(chat)

        for chat in removeChats:
            self.removeChat(chat)

    def __updateTask(self, task):
        self.update()
        return task.cont

    def addChat(self, text, playSound=True):
        lbl = OnscreenText(text, align=TextNode.ALeft, scale=self.ChatScale, wordwrap=self.ChatWordwrap,
                           fg=self.ChatColor, shadow=(0, 0, 0, 1), font=TFGlobals.getTF2SecondaryFont())
        lbl.reparentTo(self.chatRoot)
        mins = Point3()
        maxs = Point3()
        lbl.calcTightBounds(mins, maxs)
        sizeZ = maxs[2] - mins[2]
        self.chatRoot.setZ(self.chatRoot, sizeZ + self.ChatVPad)
        lbl.setZ(-self.chatRoot.getZ() + sizeZ * 0.5 + self.ChatVPad)

        if playSound:
            self.chatSound.play()

        self.chats.append(Chat(lbl, self.ChatLifetime, sizeZ))

        if len(self.chats) > self.MaxChats:
            # Remove oldest chat.
            self.removeChat(self.chats[0])

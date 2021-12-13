from direct.gui.DirectGui import DirectButton, OnscreenImage, OnscreenText
from direct.fsm.StateData import StateData

import platform
#import psutil

from panda3d.core import TextNode, TextProperties, TextPropertiesManager, ConfigVariableInt, ConfigVariableString

from tf.tfbase import TFLocalizer

import random
import sys

class TFMainMenu(StateData):

    MenuSongs = [
      "audio/bgm/gamestartup1.mp3",
      "audio/bgm/gamestartup2.mp3",
      "audio/bgm/gamestartup3.mp3"#,
      #"audio/bgm/gamestartup4.mp3",
      #"audio/bgm/gamestartup5.mp3",
      #"audio/bgm/gamestartup6.mp3",
      #"audio/bgm/gamestartup7.mp3",
      #"audio/bgm/gamestartup8.mp3",
      #"audio/bgm/gamestartup9.mp3",
      #"audio/bgm/gamestartup10.mp3",
      #"audio/bgm/gamestartup11.mp3",
      #"audio/bgm/gamestartup12.mp3",
      #"audio/bgm/gamestartup13.mp3",
      #"audio/bgm/gamestartup14.mp3",
    ]

    BgsWidescreen = ["maps/background01_widescreen.txo", "maps/background02_widescreen.txo"]
    Bgs = ["maps/background01.txo", "maps/background02.txo"]

    def __init__(self):
        StateData.__init__(self, 'MainMenuDone')
        self.buttons = []
        self.songs = []
        self.availableSongs = []
        self.logo = None
        self.bg = None
        self.verLbl = None

    def __playGame(self):
        base.request("Game", {'addr': 'http://' + ConfigVariableString('client-addr', '127.0.0.1').value + ':' + str(ConfigVariableInt('client-port', 6667).value)})

    def addMenuButton(self, text, pos, callback, extraArgs = []):
        btn = DirectButton(text = text, pos = pos, command = callback, extraArgs = extraArgs,
                           relief = None, text0_fg = (1, 1, 1, 1), text1_fg = (0.85, 0.85, 0.85, 1),
                           text2_fg = (0.85, 0.85, 0.85, 1), pressEffect = False,
                           text_align = TextNode.ALeft,
                           parent = hidden, text_scale = 0.04, text_font = base.loader.loadFont("models/fonts/tf2build.ttf"))
        self.buttons.append(btn)

    def load(self):
        StateData.load(self)
        for filename in self.MenuSongs:
            self.songs.append(base.loader.loadMusic(filename))
        self.availableSongs = list(self.songs)
        self.addMenuButton(TFLocalizer.MainMenuStartPlaying, (0.15, 0, 0), self.__playGame)
        self.addMenuButton(TFLocalizer.Quit, (0.15, 0, -0.05), sys.exit)
        self.bg = OnscreenImage(image = random.choice(self.BgsWidescreen), parent = hidden)
        #self.bg.setSx(1.77777)
        self.bg.setBin('background', 0)
        #self.bg = loader.loadModel("models/gui/title_team_widescreen")
        self.logo = OnscreenImage(image = base.loader.loadModel("models/gui/tf2_logo_2"), parent = hidden,
                                  pos = (0.57, 0, 0.2), scale = 0.04)
        self.logo.setTransparency(True)

        # Version text label.
        self.verLbl = OnscreenText(text = base.gameVersion, parent = hidden,
                                   pos = (0.04, 0.04), scale = 0.05,
                                   fg = (1, 1, 1, 1), align = TextNode.ALeft)

        gsg = base.win.getGsg()
        uname = platform.uname()
        driverInfoStr = """
        %s
        %s
        %s
        %s
        %s
        %s
        %i Ghz
        %i Threads
        %i GB Memory
        %s
        %s
        OpenGL %s
        GLSL %i.%i
        """ % (uname[0], uname[1], uname[2], uname[3], uname[4], uname[5],
             0, 0, 0,#psutil.cpu_freq().max / 1000, psutil.cpu_count(logical=True), psutil.virtual_memory().total / 1e+9,
             gsg.getDriverVendor(), gsg.getDriverRenderer(), gsg.getDriverVersion(),
             gsg.getDriverShaderVersionMajor(), gsg.getDriverShaderVersionMinor())

        self.driverInfoLbl = OnscreenText(
            text = driverInfoStr,
            parent = hidden, pos = (-0.04, 0.7), scale = 0.05, fg = (1, 1, 1, 1), align = TextNode.ARight)

    def enter(self):
        StateData.enter(self)
        self.bg.reparentTo(base.render2d)
        self.logo.reparentTo(base.a2dLeftCenter)
        self.verLbl.reparentTo(base.a2dBottomLeft)
        self.driverInfoLbl.reparentTo(base.a2dBottomRight)
        for btn in self.buttons:
            btn.reparentTo(base.a2dLeftCenter)
        self.accept("menuSongFinished", self.onMenuSongFinished)
        if not base.music:
            self.startMenuSong()
        elif base.music:
            # Carry over music from intro.
            base.music.setFinishedEvent("menuSongFinished")
            if base.music in self.availableSongs:
                self.availableSongs.remove(base.music)

    def startMenuSong(self):
        song = random.choice(self.availableSongs)
        base.playMusic(song)
        song.setFinishedEvent("menuSongFinished")

    def onMenuSongFinished(self, song):
        songWasIn = song in self.availableSongs
        if songWasIn:
            self.availableSongs.remove(song)

        if len(self.availableSongs) == 0:
            self.availableSongs = list(self.songs)
            # Remove the song that just finished from the available list just
            # this time so we don't accidentally play the same song twice in a
            # row.
            if songWasIn:
                self.availableSongs.remove(song)
            self.startMenuSong()
            if songWasIn:
                self.availableSongs.append(song)
        else:
            self.startMenuSong()

    def exit(self):
        for btn in self.buttons:
            btn.reparentTo(hidden)
        self.bg.reparentTo(hidden)
        self.logo.reparentTo(hidden)
        self.verLbl.reparentTo(hidden)
        self.driverInfoLbl.reparentTo(hidden)
        self.ignore("menuSongFinished")
        base.stopMusic()
        StateData.exit(self)

    def unload(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons = None
        self.bg.destroy()
        self.bg = None
        self.logo.destroy()
        self.logo = None
        self.verLbl.destroy()
        self.verLbl = None
        self.driverInfoLbl.destroy()
        self.driverInfoLbl = None
        self.availableSongs = None
        self.songs = None
        StateData.unload(self)

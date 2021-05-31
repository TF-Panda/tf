from direct.gui.DirectGui import DirectButton, OnscreenImage
from direct.fsm.StateData import StateData

from tf.tfbase import TFLocalizer

import random

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

    def __init__(self):
        StateData.__init__(self, 'MainMenuDone')
        self.buttons = []
        self.songs = []
        self.availableSongs = []
        self.logo = None
        self.playingSong = None

    def __playGame(self):
        base.request("Game", {'addr': 'http://127.0.0.1:6667'})

    def addMenuButton(self, text, pos, callback, extraArgs = []):
        btn = DirectButton(text = text, pos = pos, command = callback, extraArgs = extraArgs,
                           relief = None, text0_fg = (1, 1, 1, 1), text1_fg = (0.85, 0.85, 0.85, 1),
                           text2_fg = (0.85, 0.85, 0.85, 1), pressEffect = False,
                           parent = hidden, text_scale = 0.04, text_font = base.loader.loadFont("models/fonts/tf2build.ttf"))
        self.buttons.append(btn)

    def load(self):
        StateData.load(self)
        for filename in self.MenuSongs:
            self.songs.append(base.loader.loadMusic(filename))
        self.availableSongs = list(self.songs)
        self.addMenuButton(TFLocalizer.MainMenuStartPlaying, (0.3, 0, 0), self.__playGame)
        self.logo = OnscreenImage(image = base.loader.loadModel("models/gui/tf2_logo_2.bam"), parent = hidden,
                                  pos = (0.57, 0, 0.2), scale = 0.04)
        self.logo.setTransparency(True)

    def enter(self):
        StateData.enter(self)
        self.logo.reparentTo(base.a2dLeftCenter)
        for btn in self.buttons:
            btn.reparentTo(base.a2dLeftCenter)
        self.accept("menuSongFinished", self.onMenuSongFinished)
        self.startMenuSong()

    def startMenuSong(self):
        song = random.choice(self.availableSongs)
        if self.playingSong:
            self.playingSong.stop()
        self.playingSong = song
        self.playingSong.play()
        self.playingSong.setFinishedEvent("menuSongFinished")

    def onMenuSongFinished(self, song):
        self.availableSongs.remove(song)
        if len(self.availableSongs) == 0:
            self.availableSongs = list(self.songs)
            # Remove the song that just finished from the available list just
            # this time so we don't accidentally play the same song twice in a
            # row.
            self.availableSongs.remove(song)
            self.startMenuSong()
            self.availableSongs.append(song)
        else:
            self.startMenuSong()

    def exit(self):
        for btn in self.buttons:
            btn.reparentTo(hidden)
        self.logo.reparentTo(hidden)
        self.ignore("menuSongFinished")
        if self.playingSong:
            self.playingSong.stop()
            self.playingSong = None
        StateData.exit(self)

    def unload(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons = None
        self.logo.destroy()
        self.logo = None
        self.playingSong = None
        self.availableSongs = None
        self.songs = None
        StateData.unload(self)

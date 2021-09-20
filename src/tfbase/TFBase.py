from panda3d.core import *
from panda3d.pphysics import PhysScene, PhysSystem

from direct.showbase.ShowBase import ShowBase
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.gui.DirectGui import DGG, OnscreenText
from direct.directbase import DirectRender

from direct.fsm.FSM import FSM

from tf.distributed.TFClientRepository import TFClientRepository
from tf.tfbase import TFGlobals, TFLocalizer
from tf.tfgui.TFMainMenu import TFMainMenu
from tf.tfgui.NotifyView import NotifyView
from .TFPostProcess import TFPostProcess
from . import Sounds

from direct.showbase.Audio3DManager import Audio3DManager

import random

class TFBase(ShowBase, FSM):

    notify = directNotify.newCategory("TFBase")

    def __init__(self):
        ShowBase.__init__(self)
        FSM.__init__(self, 'TFBase')

        # For publishes, will be set to correct version of release in the
        # publish config.
        self.gameVersion = ConfigVariableString('tf-version', 'dev').value

        self.music = None
        self.musicFilename = None

        if self.config.GetBool('want-notify-view', 0):
            # Add text properties for the different notify levels.
            tpm = TextPropertiesManager.getGlobalPtr()
            warning = TextProperties()
            warning.setTextColor(1, 1, 0, 1)
            tpm.setProperties("warning", warning)
            error = TextProperties()
            error.setTextColor(1, 0, 0, 1)
            tpm.setProperties("error", error)
            tpm.setProperties("fatal", error)
            self.notifyView = NotifyView()

        TextNode.setDefaultFont(self.loader.loadFont("models/fonts/TF2.ttf"))

        if base.config.GetBool("want-pstats-hotkey", False):
            self.accept('shift-s', self.togglePStats)

        #self.win.disableClears()

        Sounds.loadSounds()

        self.camLens.setMinFov(base.config.GetInt("fov", 75) / (4./3.))

        self.render.setAntialias(AntialiasAttrib.MMultisample)
        self.render2d.setAntialias(AntialiasAttrib.MMultisample)
        #self.render2dp.setAntialias(AntialiasAttrib.MMultisample)
        self.pixel2d.setAntialias(AntialiasAttrib.MMultisample)

        # Set up the post-processing system
        self.postProcess = TFPostProcess()
        self.postProcess.startup(self.win)
        self.postProcess.addCamera(self.cam, 0)
        self.postProcess.setup()
        self.taskMgr.add(self.__updatePostProcess, 'updatePostProcess')

        if self.postProcess.enableHDR:
            self.render.setAttrib(LightRampAttrib.makeIdentity())

        self.musicManager.setVolume(self.config.GetFloat('music-volume', 0.1))

        self.audio3ds = []
        for mgr in base.sfxManagerList:
            mgr.setVolume(base.config.GetFloat("sfx-volume", 0.1))
            audio3d = Audio3DManager(mgr, self.cam, self.render)
            audio3d.setDistanceFactor(1/0.02032)
            self.audio3ds.append(audio3d)

        self.setBackgroundColor(0, 0, 0)
        #self.enableMouse()

        self.accept('f9', self.screenshot)

        DGG.setDefaultRolloverSound(self.loader.loadSfx("audio/sfx/buttonrollover.wav"))
        DGG.setDefaultClickSound(self.loader.loadSfx("audio/sfx/buttonclick.wav"))
        # TF2 also has a click release sound.
        DGG.setDefaultReleaseSound(self.loader.loadSfx("audio/sfx/buttonclickrelease.wav"))

        PhysSystem.ptr().initialize()
        self.physicsWorld = PhysScene()
        self.physicsWorld.setGravity((0, 0, -800)) # 9.81 m/s as inches
        self.physicsWorld.setFixedTimestep(0.015)

        #self.physicsWorld.setGroupCollisionFlag(
        #    TFGlobals.CollisionGroup.Debris, TFGlobals.CollisionGroup.Debris, False)
        self.physicsWorld.setGroupCollisionFlag(
            TFGlobals.CollisionGroup.PlayerMovement, TFGlobals.CollisionGroup.Debris, False)

        self.taskMgr.add(self.physicsUpdate, 'physicsUpdate', sort = 30)

        # Set up the view model camera and scene.
        self.vmRender = NodePath("vmrender")
        self.vmLens = PerspectiveLens()
        self.vmLens.setMinFov(self.config.GetInt("viewmodel-fov", 54) / (4./3.))
        self.vmLens.setAspectRatio(self.camLens.getAspectRatio())
        self.vmLens.setNear(1.0)
        self.vmCamera = self.makeCamera(
            self.win, lens = self.vmLens,
            clearDepth = True, clearColor = False)
        self.vmCamera.reparentTo(self.vmRender)
        self.postProcess.addCamera(self.vmCamera, 0, 2)

        self.taskMgr.add(self.viewModelSceneUpdate, 'viewModelSceneUpdate', sort = 39)

        self.playGame = None

    def playMusic(self, audio, loop=False):
        if isinstance(audio, (str, Filename)):
            self.musicFilename = audio
            audio = self.loader.loadMusic(audio)
        self.stopMusic()
        self.music = audio
        self.music.setLoop(loop)
        self.music.play()

    def stopMusic(self):
        if self.music:
            self.music.stop()
            self.music = None
        self.musicFilename = None

    def restart(self):
        ShowBase.restart(self)
        # This task is added by ShowBase automatically for the built-in
        # collision system, which we do not use.  Remove it.
        self.taskMgr.remove('resetPrevTransform')

    def togglePStats(self):
        if PStatClient.isConnected():
            PStatClient.disconnect()
        else:
            PStatClient.connect()

    def physicsUpdate(self, task):
        self.physicsWorld.simulate(globalClock.getDt())
        return task.cont

    def viewModelSceneUpdate(self, task):
        if self.render.getState() != self.vmRender.getState():
            self.vmRender.setState(self.render.getState())
        self.vmLens.setAspectRatio(self.getAspectRatio())
        self.vmCamera.setTransform(render, self.camera.getTransform(render))

        return task.cont

    def lightColor(self, light, temp, intensity):
        light.setColorTemperature(temp)
        light.setColor(Vec4(light.getColor().getXyz() * intensity, 1.0))

    def __updatePostProcess(self, task):
        self.postProcess.update()
        return task.cont

    def windowEvent(self, win):
        if win != self.win:
            # Not about our window.
            return

        # Pass it along to the postprocessing system.
        self.postProcess.windowEvent()

        ShowBase.windowEvent(self, win)

    def enterIntro(self):
        from direct.interval.IntervalGlobal import Sequence, Wait, LerpColorScaleInterval, Func
        from direct.gui.DirectGui import OnscreenImage, OnscreenText
        bgCard = CardMaker('bgCard')
        bgCard.setFrameFullscreenQuad()
        bgCardNp = self.render2d.attachNewNode(bgCard.generate())
        bgCardNp.setColor(0, 0, 0, 1)
        tfLogo = OnscreenImage(image = self.loader.loadModel("models/gui/tf2_logo_2"), scale = 0.05)
        tfLogo.setTransparency(True)
        tfLogo.setAlphaScale(0)
        pandaLogo = OnscreenImage('maps/powered_by_panda3d.txo')
        pandaLogo.setTransparency(True)
        pandaLogo.setAlphaScale(0)
        song = self.loader.loadMusic('audio/bgm/gamestartup1.mp3')
        disclaimer = OnscreenText(TFLocalizer.TFDisclaimer, scale = 0.05, wordwrap = 40,
                                  fg = (1, 1, 1, 1), pos = (0, 0.1), font = self.loader.loadFont('models/fonts/arial.ttf'))
        disclaimer.setAlphaScale(0)
        seq = Sequence()
        seq.append(Wait(0.5))
        seq.append(Func(self.playMusic, "audio/bgm/gamestartup1.mp3"))
        seq.append(Wait(0.5))
        seq.append(LerpColorScaleInterval(tfLogo, 0.75, (1, 1, 1, 1), (1, 1, 1, 0.0)))
        seq.append(Wait(1.5))
        seq.append(LerpColorScaleInterval(tfLogo, 0.5, (1, 1, 1, 0), (1, 1, 1, 1)))
        seq.append(LerpColorScaleInterval(pandaLogo, 0.75, (1, 1, 1, 1), (1, 1, 1, 0)))
        seq.append(Wait(1.5))
        seq.append(LerpColorScaleInterval(pandaLogo, 0.5, (1, 1, 1, 0), (1, 1, 1, 1)))
        seq.append(LerpColorScaleInterval(disclaimer, 0.75, (1, 1, 1, 1), (1, 1, 1, 0)))
        seq.append(Wait(5))
        seq.append(LerpColorScaleInterval(disclaimer, 0.5, (1, 1, 1, 0), (1, 1, 1, 1)))
        seq.append(Func(bgCardNp.removeNode))
        seq.append(Func(tfLogo.destroy))
        seq.append(Func(pandaLogo.destroy))
        seq.append(Func(disclaimer.destroy))
        seq.append(Func(self.request, "Preload"))
        seq.start()
        self.introSeq = seq

        self.acceptOnce('space', self.stopIntroSeq)

    def stopIntroSeq(self):
        if hasattr(self, 'introSeq'):
            self.introSeq.finish()
            del self.introSeq

    def exitIntro(self):
        self.stopIntroSeq()

    def enterPreload(self):
        # SHow a loading thing.
        cm = CardMaker('cm')
        cm.setFrameFullscreenQuad()
        cm.setHasUvs(True)
        bg = self.render2d.attachNewNode(cm.generate())
        bg.setColorScale((0.5, 0.5, 0.5, 1))
        tex = random.choice(
            ["maps/background01_widescreen.txo", "maps/background02_widescreen.txo"])
        bg.setTexture(loader.loadTexture(tex))
        bg.setBin('background', 0)

        loadingText = OnscreenText("Loading...", fg = (1, 1, 1, 1), parent = self.aspect2d)

        base.graphicsEngine.renderFrame()
        base.graphicsEngine.flipFrame()

        precacheList = [
            "models/buildables/sentry1",
            "models/char/engineer",
            "models/char/c_engineer_arms",
            "models/char/soldier",
            "models/char/c_soldier_arms",
            "models/weapons/c_rocketlauncher",
            "models/weapons/c_shotgun",
            "models/weapons/c_pistol",
            "models/weapons/c_wrench",
            "models/buildables/sentry2_heavy",
            "models/buildables/sentry2",
            "models/buildables/sentry1_gib1",
            "models/buildables/sentry1_gib2",
            "models/buildables/sentry1_gib3",
            "models/buildables/sentry1_gib4",
            "models/weapons/w_rocket",
            "models/char/demo",
            "models/char/c_demo_arms",
            "models/weapons/c_bottle",
            "models/weapons/c_shovel",
            "models/char/heavy"
        ]
        self.precache = []
        for pc in precacheList:
            self.precache.append(loader.loadModel(pc))
            # Keep the window pumping.
            base.graphicsEngine.renderFrame()

        loadingText.destroy()
        bg.removeNode()

        self.demand('MainMenu')

    def enterMainMenu(self):
        self.mainMenu = TFMainMenu()
        self.mainMenu.load()
        self.mainMenu.enter()

    def exitMainMenu(self):
        self.mainMenu.exit()
        self.mainMenu.unload()
        del self.mainMenu

    def enterGame(self, info):
        self.cl = TFClientRepository(info)
        self.cr = self.cl
        self.net = self.cl

    def exitGame(self):
        self.cl.shutdown()
        self.cl = None
        self.cr = None

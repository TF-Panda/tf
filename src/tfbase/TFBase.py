from panda3d.core import TextNode, AntialiasAttrib, LightRampAttrib, Vec4, NodePath, PerspectiveLens
from panda3d.pphysics import PhysScene, PhysSystem

from direct.showbase.ShowBase import ShowBase
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.gui.DirectGui import DGG
from direct.directbase import DirectRender

from direct.fsm.FSM import FSM

from tf.distributed.TFClientRepository import TFClientRepository
from tf.tfbase import TFGlobals
from tf.tfgui.TFMainMenu import TFMainMenu
from .TFPostProcess import TFPostProcess
from . import Sounds

from direct.showbase.Audio3DManager import Audio3DManager

class TFBase(ShowBase, FSM):

    notify = directNotify.newCategory("TFBase")

    def __init__(self):
        ShowBase.__init__(self)
        FSM.__init__(self, 'TFBase')

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
            audio3d = Audio3DManager(mgr, self.cam, self.render)
            audio3d.setDistanceFactor(1/0.02032)
            self.audio3ds.append(audio3d)

        self.setBackgroundColor(0.3, 0.3, 0.3)
        #self.enableMouse()

        TextNode.setDefaultFont(self.loader.loadFont("models/fonts/TF2.ttf"))
        DGG.setDefaultRolloverSound(self.loader.loadSfx("audio/sfx/buttonrollover.wav"))
        DGG.setDefaultClickSound(self.loader.loadSfx("audio/sfx/buttonclick.wav"))
        # TF2 also has a click release sound.
        DGG.setDefaultReleaseSound(self.loader.loadSfx("audio/sfx/buttonclickrelease.wav"))

        PhysSystem.ptr().initialize()
        self.physicsWorld = PhysScene()
        self.physicsWorld.setGravity((0, 0, -800))
        self.physicsWorld.setFixedTimestep(0.015)

        self.physicsWorld.setGroupCollisionFlag(
            TFGlobals.CollisionGroup.Debris, TFGlobals.CollisionGroup.Debris, False)

        self.taskMgr.add(self.physicsUpdate, 'physicsUpdate', sort = 30)

        # Set up the view model camera and scene.
        self.vmRender = NodePath("vmrender")
        self.vmLens = PerspectiveLens()
        self.vmLens.setMinFov(self.config.GetInt("viewmodel-fov", 54) / (4./3.))
        self.vmLens.setAspectRatio(self.camLens.getAspectRatio())
        self.vmLens.setNear(0.01)
        self.vmCamera = self.makeCamera(
            self.win, lens = self.vmLens,
            clearDepth = True, clearColor = False)
        self.vmCamera.reparentTo(self.vmRender)
        self.postProcess.addCamera(self.vmCamera, 0, 1)

        self.taskMgr.add(self.viewModelSceneUpdate, 'viewModelSceneUpdate', sort = -100)

        self.playGame = None

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

        print("hi window event")

        # Pass it along to the postprocessing system.
        self.postProcess.windowEvent()

        ShowBase.windowEvent(self, win)

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

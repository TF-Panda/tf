from panda3d.core import *
from panda3d.pphysics import *

from direct.showbase.ShowBase import ShowBase
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.gui.DirectGui import DGG, OnscreenText, OnscreenImage
from direct.directbase import DirectRender

from direct.fsm.FSM import FSM

from tf.distributed.TFClientRepository import TFClientRepository
from tf.tfbase import TFGlobals, TFLocalizer, SurfaceProperties, Soundscapes, Sounds
from tf.tfgui.TFMainMenu import TFMainMenu
from tf.tfgui.NotifyView import NotifyView
from .TFPostProcess import TFPostProcess
from .PlanarReflector import PlanarReflector
from . import Sounds
from . import Localizer

#from .Console import Console

import random

class TFBase(ShowBase, FSM):

    notify = directNotify.newCategory("TFBase")

    def __init__(self):
        ShowBase.__init__(self)
        FSM.__init__(self, 'TFBase')

        # Perform a Z-prepass on the main scene render.
        self.camNode.setTag("z_pre", "1")

       # self.render.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MEqual))

        #self.accept('shift-c', self.openConsole)

        self.console = None

        # For publishes, will be set to correct version of release in the
        # publish config.
        self.gameVersion = ConfigVariableString('tf-version', 'dev').value

        self.music = None
        self.musicFilename = None

        # Add text properties for the different notify levels.
        tpm = TextPropertiesManager.getGlobalPtr()
        warning = TextProperties()
        warning.setTextColor(1, 1, 0, 1)
        tpm.setProperties("warning", warning)
        error = TextProperties()
        error.setTextColor(1, 0, 0, 1)
        tpm.setProperties("error", error)
        tpm.setProperties("fatal", error)
        red = TextProperties()
        red.setTextColor(1, 0, 0, 1)
        blue = TextProperties()
        blue.setTextColor(0, 0, 1, 1)
        tpm.setProperties('redteam', red)
        tpm.setProperties('blueteam', blue)

        if self.config.GetBool('want-notify-view', 0):
            self.notifyView = NotifyView()

        TextNode.setDefaultFont(TFGlobals.getTF2Font())

        if base.config.GetBool("want-pstats-hotkey", False):
            self.accept('shift-s', self.togglePStats)

        self.camNode.setCameraMask(DirectRender.MainCameraBitmask)

        self.win.disableClears()

        sceneDr = self.camNode.getDisplayRegion(0)
        sceneDr.disableClears()
        sceneDr.setClearDepthActive(True)

        Sounds.loadSounds()
        SurfaceProperties.loadSurfaceProperties()
        Soundscapes.loadSoundscapes()

        self.render.hide(DirectRender.ShadowCameraBitmask)

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

        # 16 units per feet * feet per meter (3.28084)
        self.audioEngine.set3dUnitScale(52.49344)
        # Enable the steam audio listener-centric reverb on sound effects.
        base.sfxManagerList[0].setSteamAudioReverb()

        if True:#self.postProcess.enableHDR:
            self.render.setAttrib(LightRampAttrib.makeIdentity())

        # We always want to stream music.
        #self.musicManager.setStreamMode(AudioManager.SMStream)
        self.musicManager.setVolume(self.config.GetFloat('music-volume', 1))

        # We always want to preload sound effects.
        for mgr in self.sfxManagerList:
            #mgr.setStreamMode(AudioManager.SMSample)
            mgr.setVolume(base.config.GetFloat("sfx-volume", 1))

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
        self.physicsWorld.setGroupCollisionFlag(
            TFGlobals.CollisionGroup.PlayerMovement, TFGlobals.CollisionGroup.Gibs, False)
        self.physicsWorld.setGroupCollisionFlag(
            TFGlobals.CollisionGroup.Gibs, TFGlobals.CollisionGroup.Gibs, False)

        self.taskMgr.add(self.physicsUpdate, 'physicsUpdate', sort = 30)
        self.taskMgr.add(self.ragdollUpdate, 'ragdollUpdate', sort = 35)

        self.dynRender = self.render.attachNewNode(DynamicVisNode("dynamic"))

        self.sky2DTop = NodePath("sky2DTop")
        self.sky2DCam = Camera("sky2DCam")
        self.sky2DCam.setLens(self.camLens)
        self.sky2DCamNp = self.sky2DTop.attachNewNode(self.sky2DCam)
        self.sky2DDisplayRegion = self.win.makeDisplayRegion()
        self.sky2DDisplayRegion.disableClears()
        self.sky2DDisplayRegion.setClearDepthActive(True)
        self.sky2DDisplayRegion.setSort(-2)
        self.sky2DDisplayRegion.setCamera(self.sky2DCamNp)
        self.postProcess.addCamera(self.sky2DCamNp, 0, -2)

        # Separate 3-D skybox scene graph and display region.
        self.sky3DTop = NodePath("sky3DTop")
        self.sky3DTop.reparentTo(base.render)
        self.sky3DRoot = self.sky3DTop.attachNewNode("sky3DRoot")
        #self.sky3DCam = Camera("sky3DCam")
        #self.sky3DCam.setLens(self.camLens)
        #self.sky3DCamNp = self.sky3DTop.attachNewNode(self.sky3DCam)
        #self.sky3DDisplayRegion = self.win.makeDisplayRegion()
        #self.sky3DDisplayRegion.setActive(False)
        #self.sky3DDisplayRegion.disableClears()
        # Clear the depth here as this is the first display region rendered
        # for the main scene.  The actual 3D world display region clears
        # nothing.
        #self.sky3DDisplayRegion.setClearDepthActive(True)
        #self.sky3DDisplayRegion.setSort(-1)
        #self.sky3DDisplayRegion.setCamera(self.sky3DCamNp)
        #self.sky3DMat = LMatrix4.identMat()
        #self.postProcess.addCamera(self.sky3DCamNp, 0, -1)
        self.taskMgr.add(self.__update3DSkyCam, 'update3DSkyCam', sort=49)

        # Set up the view model camera and scene.
        self.vmRender = NodePath("vmrender")
        self.vmLens = PerspectiveLens()
        self.vmLens.setMinFov(self.config.GetInt("viewmodel-fov", 54) / (4./3.))
        self.vmLens.setAspectRatio(self.camLens.getAspectRatio())
        self.vmLens.setNear(1.0)
        # Clear depth to render viewmodel on top of world.
        self.vmCamera = self.makeCamera(
            self.win, lens = self.vmLens,
            clearDepth = True, clearColor = False)
        self.vmCamera.reparentTo(self.vmRender)
        self.postProcess.addCamera(self.vmCamera, 0, 2)

        self.taskMgr.add(self.viewModelSceneUpdate, 'viewModelSceneUpdate', sort = 47)

        self.playGame = None

        base.accept('shift-w', self.toggleWireframe)
        self.showingBounds = False
        self.enablePbr = False
        self.enableIk = True
        base.accept('shift-b', self.toggleBounds)
        base.accept('shift-r', ShaderManager.getGlobalPtr().reloadShaders)
        base.accept('shift-p', self.togglePbr)
        base.accept('shift-i', self.toggleIk)
        base.accept('shift-l', self.render.ls)
        base.accept('shift-k', self.vmRender.ls)
        base.accept('shift-j', self.printVMRenderMasks)

        self.planarReflect = PlanarReflector(1024, "reflection", True)
        self.planarRefract = PlanarReflector(1024, "refraction", False)

        self.enableParticles()

        # Play a constantly looping silence sound so the reverb always has
        # an input and doesn't go idle and cut off.
        self.silenceSound = self.loadSfx("audio/sfx/silence.wav")
        self.silenceSound.setLoop(True)
        self.silenceSound.play()

        #cm = CardMaker('cm')
        #cm.setHasUvs(True)
        #cm.setFrame(-1, 1, -1, 1)
        #self.csmDebug = base.aspect2d.attachNewNode(cm.generate())
        #self.csmDebug.setScale(0.3)
        #self.csmDebug.setZ(-0.7)
        #self.csmDebug.setShader(Shader.load(Shader.SL_GLSL, "shaders/debug_csm.vert.glsl", "shaders/debug_csm.frag.glsl"))

        #self.csmDebug = OnscreenImage(scale=0.3, pos=(0, 0, -0.7))

        self.lastListenerPos = Point3()
        self.taskMgr.add(self.__updateAudioListener, 'updateAudioListener', sort=51)

        self.taskMgr.add(self.__updateCharacters, 'updateCharacters', sort=46)

        self.particleMgr2 = ParticleManager2.getGlobalPtr()
        self.taskMgr.add(self.__updateParticles2, 'updateParticles2', sort=48)

        self.taskMgr.add(self.__updateDirtyDynamicNodes, 'updateDirtyDynamicNodes', sort=49)

    def printVMRenderMasks(self):
        self.r_printNodeMasks(self.vmRender.node(), 0)

    def r_printNodeMasks(self, node, indent):

        print(" " * indent, "Node", node.getName())
        print(" " * indent, "Draw show mask", node.getDrawShowMask())
        print(" " * indent, "Net draw show mask", node.getNetDrawShowMask())
        print(" " * indent, "Draw control mask", node.getDrawControlMask())
        print(" " * indent, "Net draw control mask", node.getNetDrawControlMask())

        for child in node.getChildren():
            self.r_printNodeMasks(child, indent + 2)

    def __updateCharacters(self, task):
        from tf.actor.Actor import Actor
        Actor.updateAllAnimations()
        return task.cont

    def ragdollUpdate(self, task):
        PhysRagdoll.updateRagdolls()
        return task.cont

    def __updateDirtyDynamicNodes(self, task):
        self.dynRender.node().updateDirtyChildren()
        if self.render.node().isBoundsStale():
            self.render.node().getBounds()
        if self.vmRender.node().isBoundsStale():
            self.vmRender.node().getBounds()
        return task.cont

    def __updateParticles2(self, task):
        self.particleMgr2.update(globalClock.dt)
        return task.cont

    def __updateAudioListener(self, task):
        ts = self.cam.getNetTransform()
        pos = ts.getPos()
        q = ts.getQuat()

        vel = (pos - self.lastListenerPos) / globalClock.dt

        self.audioEngine.set3dListenerAttributes(pos, q, vel)

        self.lastListenerPos = Point3(pos)

        return task.cont

    def __update3DSkyCam(self, task):
        self.sky2DCamNp.setMat(self.cam.getMat(self.render))
        #self.sky3DCamNp.setMat(self.cam.getMat(self.render) * self.sky3DMat)
        return task.cont

    def toggleIk(self):
        self.enableIk = not self.enableIk
        if self.enableIk:
            loadPrcFileData('', 'ik-enable 1')
        else:
            loadPrcFileData('', 'ik-enable 0')

    def openConsole(self):
        from .Console import Console
        if not self.console:
            self.console = Console()
        else:
            self.console.cleanup()
            self.console = None

    def togglePbr(self):
        self.enablePbr = not self.enablePbr
        if self.enablePbr:
            loadPrcFileData('', 'use-orig-source-shader 0')
        else:
            loadPrcFileData('', 'use-orig-source-shader 1')
        ShaderManager.getGlobalPtr().reloadShaders()
        print("PBR Source shader:", self.enablePbr)

    def toggleBounds(self):
        self.showingBounds = not self.showingBounds
        if self.showingBounds:
            messenger.send('show-bounds')
        else:
            messenger.send('hide-bounds')

    def playMusic(self, audio, loop=False):
        if isinstance(audio, (str, Filename)):
            self.musicFilename = audio
            audio = self.loader.loadMusic(audio, stream=True)
        self.stopMusic()
        self.music = audio
        self.music.setLoop(loop)
        self.music.play()

    def stopMusic(self):
        if self.music:
            if self.music.status() == AudioSound.PLAYING:
                # Stop the sound *only if* it's currently playing.  If this was
                # called from the finished event of the sound, calling stop()
                # again will cause an infinite loop.
                self.music.stop()
            self.music = None
        self.musicFilename = None

    def restart(self):
        ShowBase.restart(self)
        # This task is added by ShowBase automatically for the built-in
        # collision system, which we do not use.  Remove it.
        self.taskMgr.remove('resetPrevTransform')
        self.taskMgr.remove('collisionLoop')

    def togglePStats(self):
        if PStatClient.isConnected():
            PStatClient.disconnect()
        else:
            PStatClient.connect()

    def physicsUpdate(self, task):
        # Maintain an independent fixed timestep for physics
        # simulation.

        self.physicsWorld.simulate(self.clock.getFrameTime())

        if not hasattr(self, 'world'):
            return task.cont

        #soundsEmitted = 0

        chan = Sounds.Channel.CHAN_STATIC

        # Process global contact events, play sounds.
        while self.physicsWorld.hasContactEvent():
            data = self.physicsWorld.popContactEvent()

            if data.getNumContactPairs() == 0:
                continue

            pair = data.getContactPair(0)
            if not pair.isContactType(PhysEnums.CTFound):
                continue

            if pair.getNumContactPoints() == 0:
                continue

            point = pair.getContactPoint(0)

            speed = point.getImpulse().length()
            if speed < 100.0:#70.0:
                continue

            a = data.getActorA()
            b = data.getActorB()

            objA = a.getPythonTag("object")
            objB = b.getPythonTag("object")
            if objA and objA == objB:
                # Don't do impact sounds for self-collisions.
                continue

            position = point.getPosition()

            volume = speed * speed * (1.0 / (320.0 * 320.0))
            volume = min(1.0, volume)

            matA = point.getMaterialA(pair.getShapeA())
            matB = point.getMaterialB(pair.getShapeB())

            #force = speed / dt

            # Play sounds from materials of both surfaces.
            # This is more realistic, Source only played from one material.
            if matA:
                surfDefA = SurfaceProperties.SurfacePropertiesByPhysMaterial.get(matA)
            else:
                surfDefA = None
            if matB:
                surfDefB = SurfaceProperties.SurfacePropertiesByPhysMaterial.get(matB)
            else:
                surfDefB = None

            if surfDefA and surfDefB:
                # If we have an impact sound for both surfaces, divide up the
                # volume between both sounds, so impact sounds are roughly the
                # same volume as Source.
                volume *= 0.5

            if speed >= 500:
                if surfDefA:
                    base.world.emitSoundSpatial(surfDefA.impactHard, position, volume, chan=chan)
                    #soundsEmitted += 1
                if surfDefB:
                    base.world.emitSoundSpatial(surfDefB.impactHard, position, volume, chan=chan)
                    #soundsEmitted += 1
            elif speed >= 100:
                if surfDefA:
                    base.world.emitSoundSpatial(surfDefA.impactSoft, position, volume, chan=chan)
                    #soundsEmitted += 1
                if surfDefB:
                    base.world.emitSoundSpatial(surfDefB.impactSoft, position, volume, chan=chan)
                    #soundsEmitted += 1

        #if soundsEmitted > 0:
        #    print("emitted", soundsEmitted, "physics contact sounds")

        return task.cont

    def viewModelSceneUpdate(self, task):

        vmState = self.vmRender.getState()
        state = self.render.getState()
        if vmState != state:
            self.vmRender.setState(state)

        vmAr = self.vmLens.getAspectRatio()
        ar = self.getAspectRatio()
        if vmAr != ar:
            self.vmLens.setAspectRatio(ar)

        self.vmCamera.setTransform(render, self.camera.getTransform(render))

        #self.vmRender.getBounds() # Weird hack

        #print(self.vmRender.getBounds())

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
        disclaimer = OnscreenText(TFLocalizer.TFDisclaimer, scale = 0.05, wordwrap = 40,
                                  fg = (1, 1, 1, 1), pos = (0, 0.1), font = self.loader.loadFont('models/fonts/arial.ttf'))
        disclaimer.setAlphaScale(0)
        def cleanup():
            bgCardNp.removeNode()
            tfLogo.removeNode()
            pandaLogo.removeNode()
            disclaimer.removeNode()
        seq = Sequence()
        seq.append(Wait(0.5))
        seq.append(Func(self.playMusic, TFMainMenu.pickMenuSong()))
        seq.append(Wait(0.5))
        seq.append(LerpColorScaleInterval(pandaLogo, 0.75, (1, 1, 1, 1), (1, 1, 1, 0)))
        seq.append(Wait(1.5))
        seq.append(LerpColorScaleInterval(pandaLogo, 0.75, (1, 1, 1, 0), (1, 1, 1, 1)))
        seq.append(LerpColorScaleInterval(disclaimer, 0.75, (1, 1, 1, 1), (1, 1, 1, 0)))
        seq.append(Wait(3.25))
        seq.append(LerpColorScaleInterval(disclaimer, 0.75, (1, 1, 1, 0), (1, 1, 1, 1)))
        seq.append(LerpColorScaleInterval(tfLogo, 0.75, (1, 1, 1, 1), (1, 1, 1, 0.0)))
        seq.append(Wait(3))
        seq.append(LerpColorScaleInterval(tfLogo, 0.75, (1, 1, 1, 0), (1, 1, 1, 1)))
        seq.append(Func(cleanup))
        seq.setDoneEvent("introSeqDone")
        seq.start()
        self.introSeq = seq

        self.acceptOnce('introSeqDone', self.__event_introSeqDone)
        self.acceptOnce('space', self.__event_introSeqDone)

    def __event_introSeqDone(self):
        self.request('Preload')

    def stopIntroSeq(self):
        self.ignore('introSeqDone')
        self.ignore('space')
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

        aspectRatio = base.win.getXSize() / base.win.getYSize()
        if aspectRatio <= (4./3.):
            tex = random.choice(
                ["maps/background01.txo", "maps/background02.txo"])
        else:
            tex = random.choice(
                ["maps/background01_widescreen.txo", "maps/background02_widescreen.txo"])

        bg.setTexture(loader.loadTexture(tex))
        bg.setBin('background', 0)

        loadingText = OnscreenText(TFLocalizer.Loading, fg = (1, 1, 1, 1), parent = self.aspect2d)

        base.graphicsEngine.renderFrame()
        base.graphicsEngine.flipFrame()

        self.precache = []
        pgo = base.win.getGsg().getPreparedObjects()
        for pc in TFGlobals.ModelPrecacheList:
            mdl = loader.loadModel(pc)
            self.precache.append(mdl)

            #base.graphicsEngine.renderFrame()

            # Upload textures, vertex buffers, index buffers.
            mdl.prepareScene(base.win.getGsg())

            # Keep the window pumping.
            base.graphicsEngine.renderFrame()

            #pgo.beginFrameApp()

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

"""TFClassMenu: Class picker menu"""

from panda3d.core import *

from direct.gui.DirectGui import *

from tf.player.TFClass import *
from tf.tfbase import TFGlobals

from direct.interval.IntervalGlobal import Sequence, Wait, Func
from direct.interval.ActorInterval import ActorInterval

from tf.actor.Char import Char

def lightColor(light, temp, intensity):
    light.setColorTemperature(temp)
    light.setColor(Vec4(light.getColor().getXyz() * intensity, 1.0))

class TFClassMenu:

    def __init__(self):
        self.frame = DirectFrame(
          frameSize = (-0.85, 0.85, -0.65, 0.65), relief = DGG.FLAT,
          frameColor = (0, 0, 0, 0.75))
        self.frame.setBin('fixed', 0)

        self.classRoot = NodePath("ClassRenderRoot")
        self.classRoot.setAttrib(LightRampAttrib.makeIdentity())
        lens = PerspectiveLens()
        lens.setMinFov(75.0/(4./3.))
        self.classLens = lens
        self.classCam = base.makeCamera(base.win, 100, self.classRoot,
                                        clearDepth = True, clearColor = (0, 0, 0, 0),
                                        lens = lens)
        self.classCam.reparentTo(self.classRoot)
        self.classRoot.setAntialias(AntialiasAttrib.MMultisample)

        #base.setMouseOnNode(self.classCam.node())
        #self.classRoot.setH(180)

        al = AmbientLight('al')
        lightColor(al, 5500, 0.8)
        alnp = self.classRoot.attachNewNode(al)
        self.classRoot.setLight(alnp)

        dl = Spotlight('cl')
        lightColor(dl, 5000, 2.5)
        dl.setCameraMask(BitMask32.bit(2))
        #dl.setSceneCamera(base.render2d.find("**/+Camera"))
        dl.setShadowCaster(True, 4096, 4096)
        dl.setInnerCone(60)
        dl.setOuterCone(90)
        dl.setAttenuation(Vec3(0, 0, 0.0001))
        dl.setExponent(1)
        #dl.setInnerRadius(128)
        #dl.setOuterRadius(256)
        #dl.showFrustum()
        dlnp = self.classRoot.attachNewNode(dl)
        dlnp.setHpr(45, -65, 0)
        dlnp.setPos(-64, 100, 150)
        dlnp.lookAt(64, 200, -32)
        self.classRoot.setLight(dlnp)

        self.classChar = Char()
        self.weaponChar = Char()

        self.toIdleSeq = None

        self.titleLbl = OnscreenText(parent = self.frame, text = "Choose a Class", font = TFGlobals.getTF2SecondaryFont(),
                                     scale = 0.1, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 1), pos = (0, 0.55))
        self.titleLbl.setBin('fixed', 2)

        self.classButtons = []

        z = 0.3
        for classId, info in ClassInfos.items():
            btn = DirectButton(relief = None, text = info.Name,
                               text_font = TFGlobals.getTF2SecondaryFont(),
                               text_scale = 0.08,
                               parent = self.frame, text_align = TextNode.ALeft,
                               text_shadow = (0, 0, 0, 1),
                               pos = (-0.75, 0, z), text0_fg = (1, 1, 1, 1), text1_fg = (0.75, 0.75, 0.75, 1),
                               text2_fg = (0.75, 0.75, 0.75, 1), pressEffect = False,
                               command = self.pickClass, extraArgs = [classId])
            btn.setBin('fixed', 2)
            z -= 0.1
            btn.tfClassId = classId
            btn.bind(DGG.ENTER, self.onHoverClassBtn, [classId])
            self.classButtons.append(btn)
            #btn.bind(DGG.EXIT, self.onLeaveClassBtn, [classId])

        base.simTaskMgr.add(self.__charAnimEvents, "cmCharAnimEvents")
        base.taskMgr.add(self.__cmUpdatePostProcess, "cmUpdatePostProcess")

        self.pp = PostProcess()
        self.pp.startup(base.win)
        self.pp.addCamera(self.classCam, 0)
        #self.fxaa = FXAA_Effect(self.pp)
        #self.pp.addEffect(self.fxaa)
        self.bloom = BloomEffect(self.pp)
        self.pp.addEffect(self.bloom)
        self.toneMapping = ToneMappingEffect(self.pp)
        self.pp.addEffect(self.toneMapping)
        cm = CardMaker('cm')
        cm.setFrameFullscreenQuad()
        cm.setHasUvs(True)
        self.modelQuad = self.frame.attachNewNode(cm.generate())
        #self.modelQuad.hide()
        self.modelQuad.setTexture(self.pp.getOutputPipe("scene_color"))
        self.modelQuad.setBin('fixed', 1)
        self.modelQuad.setTransparency(True)

    def pickClass(self, classId):
        base.localAvatar.d_changeClass(classId)
        self.destroy()

    def destroy(self):
        if self.toIdleSeq:
            self.toIdleSeq.finish()
        del self.toIdleSeq
        self.weaponChar.clearModel()
        del self.weaponChar
        self.classChar.clearModel()
        del self.classChar
        self.modelQuad.removeNode()
        del self.modelQuad
        del self.bloom
        del self.toneMapping
        self.pp.shutdown()
        del self.pp
        base.taskMgr.remove("cmUpdatePostProcess")
        base.simTaskMgr.remove("cmCharAnimEvents")
        for btn in self.classButtons:
            btn.destroy()
        del self.classButtons
        self.titleLbl.destroy()
        del self.titleLbl
        del self.classLens
        self.classCam.removeNode()
        del self.classCam
        self.classRoot.removeNode()
        del self.classRoot
        self.frame.destroy()
        del self.frame

    def __cmUpdatePostProcess(self, task):
        self.modelQuad.setSx(base.camLens.getAspectRatio())
        self.modelQuad.setSy(1/base.camLens.getAspectRatio())
        self.classLens.setAspectRatio(base.camLens.getAspectRatio())
        self.pp.update()
        self.pp.windowEvent()
        return task.cont

    def __charAnimEvents(self, task):
        self.classChar.doAnimationEvents()
        return task.cont

    def onHoverClassBtn(self, classId, params):
        if self.toIdleSeq:
            self.toIdleSeq.finish()
            self.toIdleSeq = None

        self.weaponChar.clearModel()
        self.classChar.clearModel()

        info = ClassInfos[classId]
        self.classChar.loadModel(info.PlayerModel)
        self.classChar.setSkin(base.localAvatar.team)
        self.classChar.reparentTo(self.classRoot)
        #self.classChar.modelNp.setScale(0.01)
        self.classChar.setPos(30, 170, -48)
        self.classChar.headsUp(self.classCam)
        #self.classChar.setH(self.classChar, 180)

        for eyeNp in self.classChar.findAllMatches("**/+EyeballNode"):
            eyeNp.node().setViewTarget(self.classCam, Point3())

        self.toIdleSeq = Sequence(Func(self.classChar.play, "SelectionMenu_Anim01"),
                                  Wait(self.classChar.getDuration("SelectionMenu_Anim01")),
                                  Func(self.classChar.loop, "SelectionMenu_Idle"))
        self.toIdleSeq.start()

        if info.MenuWeapon:
            self.weaponChar.loadModel(info.MenuWeapon)
            self.weaponChar.characterNp.reparentTo(self.classChar.characterNp)
            self.weaponChar.setJointMergeCharacter(self.classChar.character)

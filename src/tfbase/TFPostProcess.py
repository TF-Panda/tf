from panda3d.core import (BloomEffect, FreezeFrameEffect, FXAA_Effect,
                          HDREffect, MotionBlur, PostProcess,
                          PostProcessFinalOutput, PTA_LVecBase3f, TextNode,
                          ToneMappingEffect, Vec3, loadPrcFileData)

from direct.gui.DirectGui import *

#
# Draw world
# Image-space motion blur
# Draw view models
# Post process

class TFPostProcess(PostProcess):

    def __init__(self):
        PostProcess.__init__(self)

        # Stages
        self.hdr = None
        self.bloom = None
        self.toneMapping = None
        self.fxaa = None
        self.ssao = None
        self.mb = None
        self.finalOutput = None
        self.freezeFrame = None

        self.camTextNode = OnscreenText("", align=TextNode.ALeft, scale=0.08, pos=(0.05, -0.15), parent=base.a2dTopLeft, fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.75), shadow=(0, 0, 0, 1))

        self.enableHDR = base.config.GetBool("hdr-enable", True)
        self.hdrDebugText = base.config.GetBool("hdr-debug-text", False)
        self.enableToneMapping = base.config.GetBool("tone-mapping-enable", True)
        self.enableBloom = base.config.GetBool("bloom-enable", True)
        self.enableSSAO = base.config.GetBool("ssao-enable", True)
        self.enableFXAA = base.config.GetBool("fxaa-enable", True)
        self.enableMB = base.config.GetBool("motion-blur-enable", False)
        self.enableVignette = base.config.GetBool("vignette-enable", False)

        self.flashEnabled = False
        self.flashColor = PTA_LVecBase3f.emptyArray(1)
        self.setFlashColor(Vec3(0))

        self.exposureBias = PTA_LVecBase3f.emptyArray(1)
        self.setExposureBias(1)

        #base.accept('f1', self.decExposureBias)
        #base.accept('f2', self.incExposureBias)

        #self.setupHBAOControls()
        if self.enableHDR and self.hdrDebugText:
            taskMgr.add(self.updateCamDebugs, "updateCamDebugs")


    def updateCamDebugs(self, task):
        text = ""

        methodVal = base.config.GetInt("hdr-exposure-auto-method")
        if methodVal == 0:
            text += "Program AE\n"
        elif methodVal == 1:
            text += "Shutter priority AE\n"
        elif methodVal == 2:
            text += "Aperture priority AE\n"
        elif methodVal == 3:
            text += "Manual Exposure\n"

        denom = self.hdr.getHdrPass().getShutterSpeed()
        if denom >= 1:
            text += f"Shutter Speed: {int(denom)}\"\n"
        elif denom > 0.0:
            text += f"Shutter Speed: 1/{int(1 / denom)}\n"
        else:
            text += f"Invalid shutter speed\n"

        apSize = self.hdr.getHdrPass().getAperature()
        text += f"Aperture: f{format(apSize, '.2f')}\n"

        isoVal = self.hdr.getHdrPass().getIso()
        text += f"ISO: {int(isoVal)}\n"

        expVal = self.hdr.getHdrPass().getExposure()
        text += f"EV: {expVal}\n"

        lumVal = self.hdr.getHdrPass().getLuminance()
        text += f"L Avg: {lumVal}\n"

        lMaxVal = self.hdr.getHdrPass().getMaxLuminance()
        text += f"L Max: {lMaxVal}\n"

        fVal = base.camLens.getFocalLength() * 25.4
        text += f"Focal Length: {int(fVal)} mm"

        self.camTextNode.setText(text)

        task.delayTime = 1.0
        return task.again

    def titleSliderBar(self, title, min, max, varname):
        def __updateVarValue(slider, title, text, varname):
            loadPrcFileData("", "{0} {1}".format(varname, slider['value']))
            text.setText("{0}: {1}".format(title, slider['value']))

        value = base.config.GetFloat(varname, min)
        frame = DirectFrame(parent = base.a2dTopLeft, pos = (0.3, 0, self.hbaoControlZ), scale = 0.3)
        titleText = OnscreenText("{0}: {1}".format(title, value), parent = frame, scale = 0.1)
        slider = DirectSlider(
            range = (min, max),
            value = value,
            command = __updateVarValue,
            pos = (0.1, 0, -0.1),
            parent = frame
        )
        slider['extraArgs'] = [slider, title, titleText, varname]

        self.hbaoControlZ -= 0.1

    def setupHBAOControls(self):
        self.titleSliderBar("Falloff", 0.05, 20, "hbao-falloff")
        self.titleSliderBar("Max sample dist", 0.05, 20, "hbao-max-sample-distance")
        self.titleSliderBar("Sample radius", 0.05, 20, "hbao-sample-radius")
        self.titleSliderBar("Angle bias", 0, 1, "hbao-angle-bias")
        self.titleSliderBar("Strength", 0, 75, "hbao-strength")

    def setExposureBias(self, bias):
        self.exposureBias[0] = bias

    def getExposureBias(self):
        return self.exposureBias[0]

    def incExposureBias(self):
        self.exposureBias[0] += 0.05
        print(self.exposureBias[0])

    def decExposureBias(self):
        self.exposureBias[0] -= 0.05
        print(self.exposureBias[0])

    def enableFlash(self, color = Vec3(0)):
        self.flashEnabled = True
        self.setFlashColor(color)

    def setFlashColor(self, color):
        self.flashColor.setElement(0, color)

    def disableFlash(self):
        self.flashEnabled = False
        self.setFlashColor(Vec3(0))

    def cleanup(self):
        if self.hdr:
            self.hdr.shutdown()
            self.removeEffect(self.hdr)
        self.hdr = None

        if self.bloom:
            self.bloom.shutdown()
            self.removeEffect(self.bloom)
        self.bloom = None

        if self.fxaa:
            self.fxaa.shutdown()
            self.removeEffect(self.fxaa)
        self.fxaa = None

        if self.ssao:
            self.ssao.shutdown()
            self.removeEffect(self.ssao)
        self.ssao = None

        if self.toneMapping:
            self.toneMapping.shutdown()
            self.removeEffect(self.toneMapping)
        self.toneMapping = None

        if self.mb:
            self.mb.shutdown()
        self.mb = None

        if self.finalOutput:
            self.finalOutput.shutdown()
        self.finalOutput = None

        if self.freezeFrame:
            self.freezeFrame.shutdown()
        self.freezeFrame = None

    def setup(self):
        self.cleanup()

        # Motion blur on top of the scene render in the same FBO.
        if self.enableMB:
            self.mb = MotionBlur(self)
            self.mb.setSceneCamera(base.cam)
            self.addEffect(self.mb)

        # Then apply bloom.
        if self.enableBloom:
            self.bloom = BloomEffect(self)
            self.addEffect(self.bloom)

        # First expose the image.
        if self.enableHDR:
            self.hdr = HDREffect(self)
            self.addEffect(self.hdr)

        # Then tone map it.
        if self.enableToneMapping:
            self.toneMapping = ToneMappingEffect(self)
            self.addEffect(self.toneMapping)

        # Then antialias it.
        if self.enableFXAA:
            self.fxaa = FXAA_Effect(self)
            self.addEffect(self.fxaa)

        #if self.enableSSAO:
        #    self.ssao = SSAO_Effect(self, SSAO_Effect.M_HBAO)
        #    self.addEffect(self.ssao)

        # Then finally, present it.
        self.finalOutput = PostProcessFinalOutput(self)
        self.addEffect(self.finalOutput)

        # Freeze frame over the final output, when needed.
        self.freezeFrame = FreezeFrameEffect(self)
        self.addEffect(self.freezeFrame)

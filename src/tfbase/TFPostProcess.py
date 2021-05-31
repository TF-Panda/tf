from panda3d.core import Shader, PTA_LVecBase3f, Vec3, loadPrcFileData, TextNode
from panda3d.core import PostProcess, PostProcessPass, PostProcessEffect, HDREffect, \
    BloomEffect, FXAA_Effect, SSAO_Effect, MotionBlur, PTA_LVecBase2f, AUXTEXTUREBITS_NORMAL, AUXTEXTURE_NORMAL, ToneMappingEffect

from direct.gui.DirectGui import *

#
# Draw world
# Image-space motion blur
# Draw view models
# Post process

class TFPostProcess(PostProcess):

    def __init__(self):
        PostProcess.__init__(self)

        self.hdr = None
        self.bloom = None
        self.toneMapping = None
        self.fxaa = None
        self.ssao = None
        self.mb = None

        self.hbaoControls = []
        self.hbaoControlZ = -0.2

        self.camDebugs = []
        self.camDebugZ = -0.2

        self.enableHDR = base.config.GetBool("hdr-enable", True)
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

        base.accept('f1', self.decExposureBias)
        base.accept('f2', self.incExposureBias)

        #self.setupHBAOControls()
        #if self.enableHDR:
        #    self.setupCamDebugs()
        #    taskMgr.add(self.updateCamDebugs, "updateCamDebugs")

    def addCamDebug(self):
        self.camDebugs.append(OnscreenText("", align = TextNode.ALeft, scale = 0.1, pos = (0.05, self.camDebugZ), parent=base.a2dTopLeft, fg = (1, 1, 1, 1), shadow=(0, 0, 0, 1)))
        self.camDebugZ -= 0.1

    def setupCamDebugs(self):
        for i in range(8):
            # Auto method, Shutter speed, aperature, ISO, exposure, luminance, lum max
            self.addCamDebug()

    def updateCamDebugs(self, task):
        method = self.camDebugs[0]
        methodVal = base.config.GetInt("hdr-exposure-auto-method")
        if methodVal == 0:
            method.setText("Program AE")
        elif methodVal == 1:
            method.setText("Shutter priority AE")
        elif methodVal == 2:
            method.setText("Aperture priority AE")
        shutter = self.camDebugs[1]
        denom = self.hdr.getHdrPass().getShutterSpeed()
        if denom >= 1:
            shutter.setText(f"Shutter Speed: {int(denom)}\"")
        else:
            shutter.setText(f"Shutter Speed: 1/{int(1 / denom)}")

        apSize = self.hdr.getHdrPass().getAperature()
        aperature = self.camDebugs[2]
        aperature.setText(f"Aperture: f{round(apSize * 2) / 2}")

        isoVal = self.hdr.getHdrPass().getIso()
        iso = self.camDebugs[3]
        iso.setText(f"ISO: {int(isoVal)}")

        expVal = self.hdr.getHdrPass().getExposureValue()
        exp = self.camDebugs[4]
        exp.setText(f"EV: {format(expVal, '.2f')}")

        lumVal = self.hdr.getHdrPass().getLuminance()
        lum = self.camDebugs[5]
        lum.setText(f"L Avg: {format(lumVal, '.2f')}")

        lMaxVal = self.hdr.getHdrPass().getMaxLuminance()
        lMax = self.camDebugs[6]
        lMax.setText(f"L Max: {format(lMaxVal, '.2f')}")

        fVal = base.camLens.getFocalLength() * 25.4
        f = self.camDebugs[7]
        f.setText(f"Focal Length: {int(fVal)} mm")

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

    def update(self):
        PostProcess.update(self)
        if self.mb:
            self.mb.update()

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

    def setup(self):
        self.cleanup()

        # First expose the image.
        if self.enableHDR:
            self.hdr = HDREffect(self)
            self.addEffect(self.hdr)

        # Then antialias it.
        if self.enableFXAA:
            self.fxaa = FXAA_Effect(self)
            self.addEffect(self.fxaa)

        # Then apply bloom.
        if self.enableBloom:
            self.bloom = BloomEffect(self)
            self.addEffect(self.bloom)

        # Then tone map it.
        if self.enableToneMapping:
            self.toneMapping = ToneMappingEffect(self)
            self.addEffect(self.toneMapping)

        #if self.enableSSAO:
        #    self.ssao = SSAO_Effect(self, SSAO_Effect.M_HBAO)
        #    self.addEffect(self.ssao)

        #if self.enableMB:
        #    self.mb = MotionBlur(self.getOutput())
        #    self.mb.setSceneCamera(base.cam)
        #    self.mb.setup()
            # sort value of 2 to do motion blur *after* the main scene,
            # which is sort 1
        #    self.addCamera(self.mb.getCamera(), 0, 1)

        finalQuad = self.getScenePass().getQuad()

        vtext = "#version 330\n"
        vtext += "uniform mat4 p3d_ModelViewProjectionMatrix;\n"
        vtext += "in vec4 p3d_Vertex;\n"
        vtext += "in vec4 texcoord;\n"
        vtext += "out vec2 l_texcoord;\n"
        vtext += "void main()\n"
        vtext += "{\n"
        vtext += "  gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;\n"
        vtext += "  l_texcoord = texcoord.xy;\n"
        vtext += "}\n"

        ptext = "#version 330\n"
        ptext += "out vec4 outputColor;\n"
        ptext += "in vec2 l_texcoord;\n"

        ptext += "uniform sampler2D sceneColorSampler;\n"

        ptext += "void main()\n"
        ptext += "{\n"
        ptext += "  outputColor = texture(sceneColorSampler, l_texcoord);\n"
        if self.enableVignette:
            ptext += "  vec2 uv = l_texcoord.xy;\n"
            ptext += "  uv *= 1.0 - uv.yx;\n"
            ptext += "  float vig = uv.x * uv.y * 15.0;\n"
            ptext += "  vig = pow(vig, 0.25);\n"
            ptext += "  outputColor.rgb *= vig;\n"
        ptext += "}\n"

        shader = Shader.make(Shader.SL_GLSL, vtext, ptext)
        if not shader:
            return

        finalQuad.setShader(shader)
        finalQuad.setShaderInput("sceneColorSampler", self.getOutputPipe("scene_color"))

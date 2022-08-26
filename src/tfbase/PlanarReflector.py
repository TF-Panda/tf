from panda3d.core import *

from direct.gui.DirectGui import *

from direct.directbase import DirectRender

class PlanarReflector:

    def __init__(self, texSize):
        self.distance = 0
        self.plane = None
        self.planeNode = None
        self.updateTask = None
        self.isSetup = False

        fbp = FrameBufferProperties()
        fbp.clear()
        fbp.setForceHardware(True)
        fbp.setFloatColor(True)
        fbp.setRgbaBits(16, 16, 16, 0)
        fbp.setDepthBits(24)

        winprops = WindowProperties()
        winprops.setSize(texSize, texSize)

        flags = GraphicsPipe.BFRefuseWindow

        self.buffer = base.graphicsEngine.makeOutput(
          base.pipe, "planar-reflection-buffer", -9000, fbp, winprops,
          flags, base.win.getGsg(), base.win)

        self.texture = Texture("planar-reflection-color")
        self.buffer.addRenderTexture(self.texture, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPColor)
        self.texture.setWrapV(SamplerState.WMClamp)
        self.texture.setWrapU(SamplerState.WMClamp)

        self.depthTexture = Texture("planar-reflection-depth")
        self.buffer.addRenderTexture(self.depthTexture, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPDepth)
        self.depthTexture.setWrapV(SamplerState.WMClamp)
        self.depthTexture.setWrapU(SamplerState.WMClamp)

        self.buffer.disableClears()

        #img = OnscreenImage(self.texture, scale =0.3, pos = (0, 0, -0.7))

        cam = base.cam.node()
        self.camera = Camera("planar-reflection-camera", cam.getLens())
        self.camera.setCameraMask(DirectRender.ReflectionCameraBitmask)
        self.cameraNP = NodePath(self.camera)

        self.displayRegion = self.buffer.makeDisplayRegion()
        self.displayRegion.disableClears()
        self.displayRegion.setClearDepthActive(True)
        self.displayRegion.setClearColorActive(True)
        self.displayRegion.setCamera(self.cameraNP)
        self.displayRegion.setActive(False)

    def renderReflection(self, node):
        ts = TextureStage("reflection")
        node.setTexture(TextureStagePool.getStage(ts), self.texture)
        #node.hide(DirectRender.ReflectionCameraBitmask)

    def setup(self, planeVec, distance, scale=1.0):
        self.shutdown()

        self.distance = distance
        self.plane = LPlane(planeVec, (0, 0, distance))
        self.planeNode = PlaneNode("planar-reflection-plane", self.plane)
        planeNP = base.render.attachNewNode(self.planeNode)
        stateNP = NodePath("statenp")
        stateNP.setClipPlane(planeNP)
        # For tinting the reflections w/o materials.
        stateNP.setColorScale((scale, scale, scale, 1.0))
        stateNP.setAttrib(CullFaceAttrib.makeReverse(), 100)
        stateNP.setAntialias(False, 100)
        self.camera.setInitialState(stateNP.getState())

        self.displayRegion.setActive(True)

        self.cameraNP.reparentTo(base.render)

        # Sort = 47 to update right before rendering.
        self.updateTask = base.taskMgr.add(self.update, "planarReflections", sort=47)

        self.isSetup = True

    def shutdown(self):
        if not self.isSetup:
            return

        self.displayRegion.setActive(False)
        self.cameraNP.reparentTo(NodePath())
        self.updateTask.remove()
        self.updateTask = None
        self.isSetup = False

    def update(self, task):
        self.cameraNP.setMat(base.cam.getMat(base.render) * self.plane.getReflectionMat())
        return task.cont

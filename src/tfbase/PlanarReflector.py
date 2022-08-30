from panda3d.core import *

from direct.gui.DirectGui import *

from direct.directbase import DirectRender

class PlanarReflector:

    def __init__(self, texSize, stageName, reflect):
        self.distance = 0
        self.plane = None
        self.planeNode = None
        self.updateTask = None
        self.isSetup = False
        self.stageName = stageName
        self.reflect = reflect
        self.texSize = texSize
        self.buffer = None

    def setupBuffer(self):
        if self.buffer:
            return

        fbp = FrameBufferProperties()
        fbp.clear()
        fbp.setForceHardware(True)
        fbp.setFloatColor(True)
        fbp.setRgbaBits(16, 16, 16, 0)
        fbp.setDepthBits(32)

        winprops = WindowProperties()
        winprops.setSize(self.texSize, self.texSize)

        flags = GraphicsPipe.BFRefuseWindow

        self.buffer = base.graphicsEngine.makeOutput(
          base.pipe, f"planar-{self.stageName}-buffer", -9000, fbp, winprops,
          flags, base.win.getGsg(), base.win)

        self.texture = Texture(f"planar-{self.stageName}-color")
        self.buffer.addRenderTexture(self.texture, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPColor)
        self.texture.setWrapV(SamplerState.WMClamp)
        self.texture.setWrapU(SamplerState.WMClamp)

        if not self.reflect:
            self.depthTexture = Texture(f"planar-{self.stageName}-depth")
            self.buffer.addRenderTexture(self.depthTexture, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPDepth)
            self.depthTexture.setWrapV(SamplerState.WMClamp)
            self.depthTexture.setWrapU(SamplerState.WMClamp)

        self.buffer.disableClears()

        #img = OnscreenImage(self.texture, scale =0.3, pos = (0, 0, -0.7))

        lens = base.camLens#.makeCopy()
        self.camera = Camera(f"planar-{self.stageName}-camera", lens)
        self.camera.setCameraMask(DirectRender.ReflectionCameraBitmask)
        #self.camera.setCullCenter(base.cam)
        self.cameraNP = NodePath(self.camera)

        #print(lens.getNear(), lens.getFar())

        self.lens = lens

        self.displayRegion = self.buffer.makeDisplayRegion()
        self.displayRegion.disableClears()
        self.displayRegion.setClearDepthActive(True)
        self.displayRegion.setClearColorActive(True)
        self.displayRegion.setCamera(self.cameraNP)
        #self.displayRegion.setActive(False)

        #self.buffer.setActive(False)

    def render(self, node):
        node.setTexture(TextureStagePool.getStage(TextureStage(self.stageName)), self.texture)
        if not self.reflect:
            node.setTexture(TextureStagePool.getStage(TextureStage(self.stageName + "_depth")), self.depthTexture)
        node.hide(DirectRender.ReflectionCameraBitmask)

    def debug(self):
        from direct.gui.DirectGui import OnscreenImage

        if not self.reflect:
            OnscreenImage(image=self.depthTexture, scale=0.3, pos=(-0.3, 0, -0.7))
            OnscreenImage(image=self.texture, scale=0.3, pos=(0.3, 0, -0.7))
        else:
            OnscreenImage(image=self.texture, scale=0.3, pos=(0, 0, -0.7))

    def setup(self, planeVec, distance, scale=1.0):
        self.setupBuffer()

        self.shutdown()

        self.distance = distance
        self.plane = LPlane(planeVec, (0, 0, distance))
        self.planeNode = PlaneNode(f"planar-{self.stageName}-plane", self.plane)
        planeNP = base.render.attachNewNode(self.planeNode)
        stateNP = NodePath("statenp")
        stateNP.setClipPlane(planeNP)
        # For tinting the reflections w/o materials.
        #stateNP.setColorScale((scale, scale, scale, 1.0))
        if self.reflect:
            stateNP.setAttrib(CullFaceAttrib.makeReverse(), 100)
        stateNP.setAntialias(False, 100)
        self.camera.setInitialState(stateNP.getState())

        #self.displayRegion.setActive(True)

        #self.buffer.setActive(True)

        self.cameraNP.reparentTo(base.render)

        # Determine PVS for reflection from position of main camera, not the
        # reflection camera.  The reflection camera is most likely flipped
        # underground into solid space.
        base.render.node().setPvsCenter(self.cameraNP.node(), base.cam)

        # Sort = 47 to update right before rendering.
        self.updateTask = base.taskMgr.add(self.update, "planar", sort=47)

        self.reflMat = self.plane.getReflectionMat()

        self.isSetup = True

    def shutdown(self):
        if not self.isSetup:
            return

        self.buffer.setActive(False)
        self.cameraNP.reparentTo(NodePath())
        base.render.node().clearPvsCenter(self.cameraNP.node())
        self.updateTask.remove()
        self.updateTask = None
        self.isSetup = False

    def update(self, task):
        mat = base.cam.getMat(render)
        if self.reflect:
            mat *= self.reflMat
        self.cameraNP.setMat(render, mat)
        return task.cont

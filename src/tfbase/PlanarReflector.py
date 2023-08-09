from panda3d.core import *

from direct.directbase import DirectRender
from direct.gui.DirectGui import *


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
        fbp.setFloatDepth(False)
        fbp.setRgbaBits(16, 16, 16, 0)
        #if not self.reflect:
            # FIXME: pipelining workaround.. we don't actually need 32 bits for depth.
        #    fbp.setDepthBits(32)
        #else:
        fbp.setDepthBits(1)
        #fbp.setDepthBits(8)

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
        self.texture.setMinfilter(SamplerState.FTLinear)
        self.texture.setMagfilter(SamplerState.FTLinear)

        if not self.reflect:
            self.depthTexture = Texture(f"planar-{self.stageName}-depth")
            #self.depthTexture.setComponentType(Texture.TUnsignedByte)
            self.buffer.addRenderTexture(self.depthTexture, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPDepth)
            self.depthTexture.setWrapV(SamplerState.WMClamp)
            self.depthTexture.setWrapU(SamplerState.WMClamp)
            self.depthTexture.setMinfilter(SamplerState.FTLinear)
            self.depthTexture.setMagfilter(SamplerState.FTLinear)

            #print(self.depthTexture)

        self.buffer.disableClears()

        #print(self.buffer.getFbProperties())

        #print("Setup frame", globalClock.frame_count)

        #img = OnscreenImage(self.texture, scale =0.3, pos = (0, 0, -0.7))

        lens = base.camLens#.makeCopy()
        self.camera = Camera(f"planar-{self.stageName}-camera", lens)
        self.camera.setCameraMask(DirectRender.ReflectionCameraBitmask)
        #self.camera.setCullCenter(base.cam)
        self.cameraNP = NodePath(self.camera)

        #print(lens.getNear(), lens.getFar())

        self.lens = lens

        self.sky2DCam = Camera("sky2DCam")
        self.sky2DCam.setLens(base.camLens)
        self.sky2DCam.setCameraMask(DirectRender.ReflectionCameraBitmask)
        self.sky2DCamNp = NodePath(self.sky2DCam)
        self.sky2DDisplayRegion = self.buffer.makeDisplayRegion()
        self.sky2DDisplayRegion.disableClears()
        self.sky2DDisplayRegion.setClearDepthActive(True)
        self.sky2DDisplayRegion.setSort(-2)
        self.sky2DDisplayRegion.setCamera(self.sky2DCamNp)

        # Separate 3-D skybox scene graph and display region.
        self.sky3DCam = Camera("sky3DCam")
        self.sky3DCam.setLens(base.camLens)
        self.sky3DCam.setCameraMask(DirectRender.ReflectionCameraBitmask)
        self.sky3DCamNp = NodePath(self.sky3DCam)
        self.sky3DDisplayRegion = self.buffer.makeDisplayRegion()
        #self.sky3DDisplayRegion.setActive(False)
        self.sky3DDisplayRegion.disableClears()
        # Clear the depth here as this is the first display region rendered
        # for the main scene.  The actual 3D world display region clears
        # nothing.
        self.sky3DDisplayRegion.setClearDepthActive(True)
        self.sky3DDisplayRegion.setSort(-1)
        self.sky3DDisplayRegion.setCamera(self.sky3DCamNp)

        self.displayRegion = self.buffer.makeDisplayRegion()
        self.displayRegion.disableClears()
        self.displayRegion.setClearDepthActive(True)
        #self.displayRegion.setClearColorActive(True)
        self.displayRegion.setCamera(self.cameraNP)
        #self.displayRegion.setActive(False)

        self.buffer.setActive(False)

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
        self.sky3DCamNp.node().setInitialState(stateNP.getState())
        self.sky2DCamNp.node().setInitialState(stateNP.getState())

        #self.displayRegion.setActive(True)

        if ConfigVariableBool('tf-water-reflections', False).value:
            self.buffer.setActive(True)

        self.cameraNP.reparentTo(base.render)
        self.sky2DCamNp.reparentTo(base.sky2DTop)
        self.sky3DCamNp.reparentTo(base.sky3DTop)

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
        self.sky2DCamNp.setMat(render, mat)
        self.sky3DCamNp.setMat(render, mat * base.sky3DMat)
        return task.cont

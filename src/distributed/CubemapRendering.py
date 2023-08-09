"""CubemapRendering module: contains the CubemapRendering class."""

from panda3d.core import *

from direct.directbase import DirectRender

CubeFaces = [
  # Positive X
  {"look_at": (1, 0, 0), "up": (0, -1, 0)},
  # Negative X
  {"look_at": (-1, 0, 0), "up": (0, -1, 0)},
  # Positive Y
  {"look_at": (0, 1, 0), "up": (0, 0, 1)},
  # Negative Y
  {"look_at": (0, -1, 0), "up": (0, 0, -1)},
  # Positive Z
  {"look_at": (0, 0, 1), "up": (0, -1, 0)},
  # Negative Z
  {"look_at": (0, 0, -1), "up": (0, -1, 0)}
]

class CubemapRendering:


    def __init__(self):
        self.camRoot = None
        self.faceCams = []

    def renderCubemap(self, mcm):
        # Position the camera rig at the cubemap.
        self.camRoot.setPos(mcm.getPos())

        tex = mcm.getTexture()

        # Create a new offscreen buffer to render this cubemap.
        fbProps = FrameBufferProperties()
        fbProps.clear()
        fbProps.setRgbaBits(32, 32, 32, 0)
        fbProps.setDepthBits(8)
        fbProps.setForceHardware(True)
        fbProps.setFloatColor(True)
        fbProps.setSrgbColor(False)
        flags = GraphicsPipe.BFRefuseWindow  | GraphicsPipe.BFSizeSquare | GraphicsPipe.BFRefuseParasite
        buffer = base.graphicsEngine.makeOutput(
          base.pipe, "cubemap-render", 10, fbProps, WindowProperties.size(mcm.getSize(), mcm.getSize()), flags,
          base.win.getGsg(), base.win
        )
        assert buffer
        # Render into the cubemap texture.
        buffer.addRenderTexture(tex, GraphicsOutput.RTMCopyRam, GraphicsOutput.RTPColor)
        buffer.disableClears()
        buffer.setSort(10)

        displayRegions = []

        dirLight = base.game.lvlData.getDirLight()

        # Now create display regions for each of the cube map faces.
        for i in range(6):
            dr = buffer.makeDisplayRegion()
            dr.setTargetTexPage(i)
            dr.setCamera(self.faceCams[i])
            dr.disableClears()
            dr.setClearDepthActive(True)
            dr.setActive(False)
            displayRegions.append(dr)

        for i in range(6):
            dr = displayRegions[i]

            if not dirLight.isEmpty():
                # Update cascades for this cube map face camera.
                dirLight.node().setSceneCamera(self.faceCams[i])
                dirLight.node().update(base.render)

            dr.setActive(True)
            # Render to this face.
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.syncFrame()
            dr.setActive(False)

        print(tex)

        #base.graphicsEngine.extractTextureData(tex, base.win.getGsg())
        #tex.write(Notify.out(), 0)
        #ret = tex.write("cubemap-" + str(mcm.getPos()) + "-#.png", 0, 0, True, False)
        #print(ret)

        # Clean up.
        base.graphicsEngine.removeWindow(buffer)

        if not dirLight.isEmpty():
            dirLight.node().setSceneCamera(base.cam)

    def renderCubemaps(self, lvlData):
        # Don't render dynamic objects.
        base.dynRender.hide()

        camRoot = base.render.attachNewNode('cubeMapCamRig')
        self.camRoot = camRoot

        # Create the cube map camera rig.
        lens = PerspectiveLens(90, 90)
        for i in range(6):
            camera = Camera('cubemap-cam-' + str(i))
            camera.setLens(lens)
            camera.setCameraMask(DirectRender.MainCameraBitmask)
            cameraNp = camRoot.attachNewNode(camera)
            cameraNp.lookAt(CubeFaces[i]["look_at"], CubeFaces[i]["up"])
            self.faceCams.append(cameraNp)

        for i in range(lvlData.getNumCubeMaps()):
            mcm = lvlData.getCubeMap(i)
            self.renderCubemap(mcm)

        # TODO: Copy cube map textures into RAM, write out level file.

        for cam in self.faceCams:
            cam.removeNode()
        self.faceCams = None

        self.camRoot.removeNode()
        self.camRoot = None

        base.dynRender.show()

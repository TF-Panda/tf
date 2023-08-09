"""DistributedPointSpotlight module: contains the DistributedPointSpotlight class."""

from panda3d.core import *

from direct.directbase import DirectRender

from .DistributedEntity import DistributedEntity


class DistributedPointSpotlight(DistributedEntity):
    """
    A spotlight beam effect with a sprite halo at the top.
    """

    def __init__(self):
        DistributedEntity.__init__(self)
        self.spotlightLength = 1
        self.spotlightWidth = 1
        self.spotlightDir = Vec3.down()
        self.negSpotlightDir = Vec3.up()
        self.rgbColor = Vec3(0)

        self.brightnessFactor = 125.0 / 255.0

        if IS_CLIENT:
            self.spotlight = None
            #self.halo = None

    if not IS_CLIENT:
        def initFromLevel(self, ent, props):
            DistributedEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("spotlightlength"):
                self.spotlightLength = props.getAttributeValue("spotlightlength").getFloat()
            if props.hasAttribute("spotlightwidth"):
                self.spotlightWidth = props.getAttributeValue("spotlightwidth").getFloat()
            if props.hasAttribute("rendercolor"):
                self.rgbColor = KeyValues.to3f(props.getAttributeValue("rendercolor").getString())

            self.spotlightDir = self.getQuat().getForward()

    else:
        def RecvProxy_rgbColor(self, r, g, b):
            self.rgbColor[0] = r / 255.0
            self.rgbColor[1] = g / 255.0
            self.rgbColor[2] = b / 255.0

        def announceGenerate(self):
            DistributedEntity.announceGenerate(self)

            self.reparentTo(base.dynRender)

            #mins = Point3(-self.spotlightWidth, -self.spotlightWidth, -self.spotlightLength)
            #maxs = Point3(self.spotlightWidth, self.spotlightWidth, 0)
            #self.node().setBounds(BoundingBox(mins, maxs))
            self.node().setFinal(True)
            #self.showBounds()

            self.spotlightDir = Vec3(self.spotlightDir[0], self.spotlightDir[1], self.spotlightDir[2])

            self.negSpotlightDir = -self.spotlightDir

            self.hide(DirectRender.ShadowCameraBitmask)
            #self.hide(DirectRender.ReflectionCameraBitmask)

            clbkNode = SpotlightBeam("spotlight-callback")
            clbkNode.setBeamColor(self.rgbColor * self.brightnessFactor)
            clbkNode.setBeamSize(self.spotlightLength, self.spotlightWidth)
            clbkNode.setHaloColor(self.rgbColor)
            clbkNode.setHaloSize(75)
            root = self.attachNewNode(clbkNode)
            spotlight = root.attachNewNode("spotlight")
            spotlight.setP(90)

            # Create sprite card for the spotlight beam.
            cm = CardMaker("beam")
            cm.setFrame(-1, 1, -1.0, 0.0)
            cm.setHasUvs(True)
            beamNp = spotlight.attachNewNode(cm.generate())
            beamNp.setMaterial(base.loader.loadMaterial("materials/glow_test02.mto"))
            beamNp.setSz(self.spotlightLength)
            beamNp.setSx(self.spotlightWidth)
            beamNp.setBillboardAxis()

            cm = CardMaker("halo")
            cm.setFrame(-1, 1, -1, 1)
            cm.setHasUvs(True)

            haloNp = root.attachNewNode(cm.generate())
            haloNp.setBillboardPointEye()
            haloNp.setMaterial(base.loader.loadMaterial("materials/light_glow03.mto"))
            haloNp.setDepthTest(False, 1)
            haloNp.setDepthWrite(False, 1)

            self.spotlight = root

            #self.addTask(self.__update, "updatePointSpotlight", )

        def disable(self):
            if self.spotlight:
                self.spotlight.removeNode()
                self.spotlight = None
            #if self.halo:
            #    self.halo.removeNode()
            #    self.halo = None
            DistributedEntity.disable(self)

if not IS_CLIENT:
    DistributedPointSpotlightAI = DistributedPointSpotlight
    DistributedPointSpotlightAI.__name__ = 'DistributedPointSpotlightAI'

"""DistributedPointSpotlight module: contains the DistributedPointSpotlight class."""

from .DistributedEntity import DistributedEntity

from panda3d.core import Vec3, CardMaker, CallbackNode, CallbackObject, KeyValues, SpriteGlow

from direct.directbase import DirectRender

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

        self.brightnessFactor = 100.0 / 255.0

        if IS_CLIENT:
            self.spotlight = None
            self.halo = None

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

        def setBeamHaloFactor(self, blend):
            if blend <= 0.001:
                self.spotlight.hide()
                self.halo.show()
            elif blend >= 0.999:
                self.spotlight.show()
                self.halo.hide()
            else:
                self.spotlight.show()
                self.halo.show()

            self.spotlight.setColorScale(self.rgbColor * (1.0 - blend) * self.brightnessFactor)
            self.halo.setColorScale(self.rgbColor * self.brightnessFactor)

        def cullCallback(self, cbdata):
            camToLight = self.getPos() - base.cam.getPos(base.render)
            camToLight.normalize()

            factor = abs(camToLight.z)

            #print("factor", factor)

            self.setBeamHaloFactor(factor)

            cbdata.upcall()

        def announceGenerate(self):
            DistributedEntity.announceGenerate(self)

            self.reparentTo(base.render)
            self.showBounds()

            self.spotlightDir = Vec3(self.spotlightDir[0], self.spotlightDir[1], self.spotlightDir[2])

            self.negSpotlightDir = -self.spotlightDir

            self.hide(DirectRender.ShadowCameraBitmask)
            #self.hide(DirectRender.ReflectionCameraBitmask)

            clbkNode = CallbackNode("spotlight-callback")
            clbkNode.setCullCallback(CallbackObject.make(self.cullCallback))
            self.spotlight = self.attachNewNode(clbkNode)
            self.spotlight.setP(90)

            # Create sprite card for the spotlight beam.
            cm = CardMaker("beam")
            cm.setFrame(-1, 1, -1.0, 0.0)
            cm.setHasUvs(True)
            beamNp = self.spotlight.attachNewNode(cm.generate())
            beamNp.setMaterial(base.loader.loadMaterial("tfmodels/src/materials/glow_test02.pmat"))
            beamNp.setSz(self.spotlightLength)
            beamNp.setSx(self.spotlightWidth)
            beamNp.setBillboardAxis()

            #cm = CardMaker("halo")
            #cm.setFrame(-1, 1, -1, 1)
            #cm.setHasUvs(True)

            self.halo = self.attachNewNode("halo")#SpriteGlow("halo", 60))
            #self.halo.setBillboardPointEye()
            #haloNp = self.halo.attachNewNode(cm.generate())
            #haloNp.setScale(60)
            #haloNp.setMaterial(base.loader.loadMaterial("tfmodels/src/materials/light_glow03.pmat"))

        def disable(self):
            if self.spotlight:
                self.spotlight.removeNode()
                self.spotlight = None
            if self.halo:
                self.halo.removeNode()
                self.halo = None
            DistributedEntity.disable(self)

if not IS_CLIENT:
    DistributedPointSpotlightAI = DistributedPointSpotlight
    DistributedPointSpotlightAI.__name__ = 'DistributedPointSpotlightAI'

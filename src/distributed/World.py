from tf.entity.DistributedEntity import DistributedEntity

from panda3d.core import *
from panda3d.pphysics import *

from direct.directbase import DirectRender
from tf.tfbase.TFGlobals import Contents, TakeDamage

from math import pow

class World(DistributedEntity):

    def __init__(self):
        DistributedEntity.__init__(self)
        self.takeDamageMode = TakeDamage.No

    def rgb255Scalar(self, r, g, b, scalar):
        v = Vec3(pow(r/255, 2.2), pow(g/255, 2.2), pow(b/255, 2.2))
        v *= (scalar/255)
        return Vec4(v, 1.0)

    def createWorld(self):
        al = AmbientLight('al')
        al.setColor(self.rgb255Scalar(200, 202, 230, 150 * 5000))
        alnp = render.attachNewNode(al)
        self.alnp = alnp
        render.setLight(alnp)

        dl = CascadeLight('cl')
        dl.setColor(self.rgb255Scalar(216, 207, 194, 700 * 5000))
        dl.setCameraMask(DirectRender.ShadowCameraBitmask)
        dl.setSceneCamera(base.cam)
        dl.setShadowCaster(True, 4096, 4096)
        dlnp = render.attachNewNode(dl)
        dlnp.setHpr(145 - 90, -45, 0)
        self.dlnp = dlnp
        render.setLight(dlnp)

        render.setAttrib(LightRampAttrib.makeHdr0())

        skycard = CardMaker('sky')
        skycard.setFrame(-0.5, 0.5, -0.5, 0.5)
        skycard.setHasUvs(True)
        skycard.setHasNormals(True)
        skynp = NodePath(skycard.generate())
        skynp.setShader(Shader.load(Shader.SL_GLSL, "shaders/skybox.vert.glsl", "shaders/skybox.frag.glsl"))
        skynp.setShaderInput("skyboxSampler", loader.loadTexture("/c/Users/brian/ttsp/game/resources/materials/sky/sky.ptex"))

        skynpRoot = render.attachNewNode("skyroot")
        skynpRoot.setScale(500 * 16)
        #skynpRoot.setLightOff(1)
        #skynpRoot.setColorScale((4000, 4000, 4000, 1))
        skynpRoot.hide(DirectRender.ShadowCameraBitmask)

        skynpFront = skynp.copyTo(skynpRoot)
        skynpFront.setY(0.5)

        skynpBack = skynp.copyTo(skynpRoot)
        skynpBack.setY(-0.5)
        skynpBack.setH(180)

        skynpLeft = skynp.copyTo(skynpRoot)
        skynpLeft.setX(0.5)
        skynpLeft.setH(-90)

        skynpRight = skynp.copyTo(skynpRoot)
        skynpRight.setX(-0.5)
        skynpRight.setH(90)

        skynpTop = skynp.copyTo(skynpRoot)
        skynpTop.setZ(-0.5)
        skynpTop.setP(-90)

        skynpBot = skynp.copyTo(skynpRoot)
        skynpBot.setZ(0.5)
        skynpBot.setP(90)

        groundCm = CardMaker('ground')
        size = 2048
        groundCm.setFrame(-size, size, -size, size)
        groundCm.setUvRange(Vec2(0), Vec2(size / 32))
        groundCm.setHasUvs(True)
        groundCm.setHasNormals(True)
        ground = render.attachNewNode(groundCm.generate())
        ground.setMaterial(MaterialPool.loadMaterial("tfmodels/src/maps/concretefloor01.pmat"))
        ground.setP(-90)

    def deleteWorld(self):
        render.clearLight(self.alnp)
        render.clearLight(self.dlnp)
        self.alnp.removeNode()
        del self.alnp
        self.dlnp.removeNode()
        del self.dlnp

    def delete(self):
        if IS_CLIENT:
            self.deleteWorld()

        self.lvl.removeNode()
        del self.lvl

        DistributedEntity.delete(self)

    def generate(self):
        DistributedEntity.generate(self)

        if IS_CLIENT:
            self.createWorld()

        planeMat = PhysMaterial(0.4, 0.25, 0.2)
        planeShape = PhysShape(PhysPlane(LPlane(0, 0, 1, 0)), planeMat)
        planeActor = PhysRigidStaticNode("plane")
        planeActor.addShape(planeShape)
        planeActor.addToScene(base.physicsWorld)
        planeActor.setContentsMask(Contents.Solid)
        planeNp = base.render.attachNewNode(planeActor)
        planeNp.setPos(0, 0, 0)
        planeNp.setPythonTag("entity", self)

        """
        self.lvl = base.loader.loadModel("ctf_2fort.bam")
        self.lvl.reparentTo(base.render)
        data = self.lvl.find("**/+MapRoot").node().getData()
        for i in range(data.getNumModelPhysDatas()):
            meshBuffer = data.getModelPhysData(i)
            if len(meshBuffer) == 0:
                continue
            meshData = PhysTriangleMeshData(meshBuffer)
            geom = PhysTriangleMesh(meshData)
            shape = PhysShape(geom, PhysMaterial(0.4, 0.25, 0.2))
            body = PhysRigidStaticNode("model-phys-%i" % i)
            body.addShape(shape)
            body.setContentsMask(Contents.Solid)
            body.addToScene(base.physicsWorld)
            body.setPythonTag("entity", self)
            self.lvl.attachNewNode(body)
        """

if not IS_CLIENT:
    WorldAI = World
    WorldAI.__name__ = 'WorldAI'

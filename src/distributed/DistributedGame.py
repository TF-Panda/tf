""" DistributedGame module: contains the DistributedGame class """

from direct.distributed2.DistributedObject import DistributedObject

from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase import Sounds

class DistributedGame(DistributedObject):

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        self.sendUpdate("joinGame", ['Brian'])

        al = AmbientLight('al')
        base.lightColor(al, 7000, 4000)
        alnp = render.attachNewNode(al)
        render.setLight(alnp)

        skycard = CardMaker('sky')
        skycard.setFrame(-0.5, 0.5, -0.5, 0.5)
        skycard.setHasUvs(True)
        skycard.setHasNormals(True)
        skynp = NodePath(skycard.generate())
        skynp.setShader(Shader.load(Shader.SL_GLSL, "shaders/skybox.vert.glsl", "shaders/skybox.frag.glsl"))
        skynp.setShaderInput("skyboxSampler", loader.loadTexture("/c/Users/brian/ttsp/game/resources/materials/sky/sky.ptex"))

        skynpRoot = render.attachNewNode("skyroot")
        skynpRoot.setScale(500 * 16)
        skynpRoot.setLightOff(1)
        skynpRoot.setColorScale((4000, 4000, 4000, 1))
        skynpRoot.hide(BitMask32.bit(1))

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

        dl = CascadeLight('cl')
        base.lightColor(dl, 5000, 15000)
        dl.setCameraMask(BitMask32.bit(1))
        dl.setSceneCamera(base.cam)
        dl.setShadowCaster(True, 4096, 4096)
        dlnp = render.attachNewNode(dl)
        dlnp.setHpr(45, -65, 0)
        render.setLight(dlnp)

        render.show(BitMask32.bit(1))

        render.setAttrib(LightRampAttrib.makeHdr0())

        groundCm = CardMaker('ground')
        size = 2048
        groundCm.setFrame(-size, size, -size, size)
        groundCm.setUvRange(Vec2(0), Vec2(size / 32))
        groundCm.setHasUvs(True)
        groundCm.setHasNormals(True)
        ground = render.attachNewNode(groundCm.generate())
        ground.setMaterial(MaterialPool.loadMaterial("tfmodels/src/maps/concretefloor01.pmat"))
        ground.setP(-90)

        planeMat = PhysMaterial(0.4, 0.25, 0.2)
        planeShape = PhysShape(PhysPlane(LPlane(0, 0, 1, 0)), planeMat)
        planeActor = PhysRigidStaticNode("plane")
        planeActor.addShape(planeShape)
        planeActor.addToScene(base.physicsWorld)
        planeNp = render.attachNewNode(planeActor)
        planeNp.setPos(0, 0, 0)

        base.game = self

    def delete(self):
        del base.game
        DistributedObject.delete(self)

    def emitSound(self, soundIndex, waveIndex, volume, pitch, origin):
        sound = Sounds.createSoundClient(soundIndex, waveIndex, volume, pitch, origin)
        if sound:
            sound.play()


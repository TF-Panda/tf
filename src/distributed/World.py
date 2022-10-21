from tf.entity.DistributedSolidEntity import DistributedSolidEntity

from panda3d.core import *
from panda3d.pphysics import *

from direct.directbase import DirectRender

from tf.tfbase.TFGlobals import Contents, TakeDamage, SolidShape, SolidFlag, WorldParent
from tf.tfbase.SurfaceProperties import SurfaceProperties

class World(DistributedSolidEntity):

    MakeFinal = False

    def __init__(self):
        DistributedSolidEntity.__init__(self)
        self.takeDamageMode = TakeDamage.No

        self.solidShape = SolidShape.Model
        self.solidFlags = SolidFlag.Tangible
        self.physType = self.PTTriangles
        self.parentEntityId = WorldParent.Render

        self.worldCollisions = []

    def initWorldCollisions(self):
        collideTypeToMask = {
            "": Contents.Solid,
            "clip": Contents.PlayerSolid,
            "playerclip": Contents.PlayerSolid
        }
        for i in range(self.model.getNumTriGroups()):
            group = self.model.getTriGroup(i)
            triMesh = PhysTriangleMesh(PhysTriangleMeshData(group.getTriMeshData()))
            materials = []
            for i in range(group.getNumSurfaceProps()):
                materials.append(SurfaceProperties[group.getSurfaceProp(i).lower()].getPhysMaterial())

            shape = PhysShape(triMesh, materials[0])
            shape.setSceneQueryShape(True)
            shape.setSimulationShape(True)
            shape.setTriggerShape(False)

            # Append remaining materials if there are multiple.
            if len(materials) > 1:
                for i in range(1, len(materials)):
                    shape.addMaterial(materials[i])

            body = PhysRigidStaticNode("world-collide-" + group.getCollideType())
            body.setContentsMask(collideTypeToMask.get(group.getCollideType(), Contents.Solid))
            body.addShape(shape)
            body.addToScene(base.physicsWorld)
            body.setPythonTag("entity", self)
            body.setPythonTag("object", self)
            self.attachNewNode(body)
            self.worldCollisions.append(body)

    def generate(self):
        DistributedSolidEntity.generate(self)
        base.world = self

        # Link static prop physics to world entity.
        for np in base.game.propPhysRoot.findAllMatches("**/+PhysRigidActorNode"):
            np.setPythonTag("entity", self)
            np.setPythonTag("object", self)

    def announceGenerate(self):
        DistributedSolidEntity.announceGenerate(self)
        #self.initializeCollisions()
        #self.node().setCcdEnabled(True)

        self.initWorldCollisions()

        # Enable Z-prepass on the world geometry.
        self.setAttrib(DepthPrepassAttrib.make(DirectRender.MainCameraBitmask|DirectRender.ReflectionCameraBitmask))
        self.flattenLight()

    def delete(self):
        for body in self.worldCollisions:
            body.removeFromScene(base.physicsWorld)
        self.worldCollisions = None
        base.world = None
        DistributedSolidEntity.delete(self)

if not IS_CLIENT:
    WorldAI = World
    WorldAI.__name__ = 'WorldAI'

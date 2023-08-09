import random

from panda3d.core import *
from panda3d.pphysics import *

from direct.directbase import DirectRender
from tf.entity.DistributedSolidEntity import DistributedSolidEntity
from tf.tfbase import CollisionGroups
from tf.tfbase.SurfaceProperties import SurfaceProperties
from tf.tfbase.TFGlobals import SolidFlag, SolidShape, TakeDamage, WorldParent


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

    def traceDecal(self, decalName, tr, excludeClients=[], client=None):
        if not decalName:
            return
        propIndex = -1
        actor = tr['actor']
        if actor:
            propIndex = actor.getPythonTag("propIndex")
            if propIndex is None:
                propIndex = -1
        if IS_CLIENT:
            self.projectDecalWorld(decalName, tr['endpos'], tr['norm'], random.uniform(0, 360), propIndex)
        else:
            self.sendUpdate('projectDecalWorld', [decalName, tr['endpos'], tr['norm'], random.uniform(0, 360), propIndex],
                            client=client, excludeClients=excludeClients)

    if IS_CLIENT:

        def parentDecal(self, np):
            np.reparentTo(self.decalVisRootNp)

        def projectDecalWorld(self, decalName, position, normal, roll, propIndex):
            if propIndex >= 0:
                decalRoot = base.game.propModels[propIndex]
            else:
                decalRoot = self.modelNp
            self.projectDecal(decalName, position, normal, roll, decalRoot)

    def initWorldCollisions(self):
        collideTypeToMask = {
            "": CollisionGroups.World,
            "clip": CollisionGroups.PlayerClip,
            "playerclip": CollisionGroups.PlayerClip,
            "sky": CollisionGroups.Sky
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
                shape.submitMaterials()

            body = PhysRigidStaticNode("world-collide-" + group.getCollideType())
            body.setFromCollideMask(collideTypeToMask.get(group.getCollideType(), CollisionGroups.World))
            body.addShape(shape)
            body.addToScene(base.physicsWorld)
            body.setPythonTag("entity", self)
            body.setPythonTag("object", self)
            self.attachNewNode(body)
            self.worldCollisions.append(body)

    def generate(self):
        DistributedSolidEntity.generate(self)
        base.world = self

        # Create a dedicated node for culling decals placed on the world
        # against the PVS, since the world itself is not PVS culled.
        # Decals on other entities are culled along with the entity
        # implicitly.
        self.decalVisRoot = DynamicVisNode("world-decal-root")
        self.decalVisRoot.levelInit(base.game.lvlData.getNumClusters(), base.game.lvlData.getAreaClusterTree())
        self.decalVisRootNp = base.render.attachNewNode(self.decalVisRoot)

        if IS_CLIENT:
            self.addTask(self.__updateDecalVis, 'updateDecalVis', sim=False, appendTask=True, sort=49)

        # Link static prop physics to world entity.
        for np in base.game.propPhysRoot.findAllMatches("**/+PhysRigidActorNode"):
            np.setPythonTag("entity", self)
            np.setPythonTag("object", self)

    def __updateDecalVis(self, task):
        if not self.decalVisRoot:
            return task.done
        self.decalVisRoot.updateDirtyChildren()
        return task.cont

    def announceGenerate(self):
        DistributedSolidEntity.announceGenerate(self)
        #self.initializeCollisions()
        #self.node().setCcdEnabled(True)

        self.initWorldCollisions()

        # Enable Z-prepass on the world geometry.
        if base.config.GetBool('tf-do-z-prepass', True):
            self.setAttrib(DepthPrepassAttrib.make(DirectRender.MainCameraBitmask|DirectRender.ReflectionCameraBitmask))
        self.flattenLight()

        """
        if IS_CLIENT and self.modelNp:
            # The world contains lots of triangles (func_details, displacements, world brushes).
            # Build an octree out of the triangles to accelerate decal
            # placement on the world.
            gn = self.modelNp.node()
            for geom in gn.getGeoms():
                octree = GeomTriangleOctree()
                octree.build(geom, Vec3(32), 20)
                DecalProjector.setGeomOctree(geom, octree)
        """

    def delete(self):
        if self.modelNp:
            for geom in self.modelNp.node().getGeoms():
                DecalProjector.clearGeomOctree(geom)
        self.decalVisRootNp.removeNode()
        self.decalVisRootNp = None
        self.decalVisRoot = None
        for body in self.worldCollisions:
            body.removeFromScene(base.physicsWorld)
        self.worldCollisions = None
        base.world = None
        DistributedSolidEntity.delete(self)

if not IS_CLIENT:
    WorldAI = World
    WorldAI.__name__ = 'WorldAI'

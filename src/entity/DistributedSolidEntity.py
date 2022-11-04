"""DistributedSolidEntity module: contains the DistributedSolidEntity class."""

from panda3d.core import *
from panda3d.pphysics import *

from .DistributedEntity import DistributedEntity
from tf.tfbase.SurfaceProperties import SurfaceProperties
from tf.tfbase import TFGlobals

class DistributedSolidEntity(DistributedEntity):
    """
    An entity associated with a solid/brush/mesh authored in the level.
    """

    # The brush physics mesh to use for the entity.  Use convex for
    # volume entities like triggers, triangles for solid and visible
    # entities.
    PTNone = 0
    PTConvex = 1
    PTTriangles = 2

    # True if the entity should be positioned at the center of the
    # model's bounding box, or False to leave it at the world origin.
    NeedOrigin = False

    def __init__(self):
        DistributedEntity.__init__(self, False)
        self.setLightOff(-1)
        self.modelNum = 0
        self.model = None
        self.modelNp = None
        self.physType = self.PTNone
        self.modelOrigin = TransformState.makeIdentity()
        self.renderMode = 0

    if not IS_CLIENT:
        def initFromLevel(self, ent, properties):
            DistributedEntity.initFromLevel(self, ent, properties)
            self.modelNum = ent.getModelIndex()
            if properties.hasAttribute("rendermode"):
                self.renderMode = properties.getAttributeValue("rendermode").getInt()

    def makeModelCollisionShape(self):
        invOrigin = self.modelOrigin.getInverse().getPos()

        if self.physType == self.PTConvex:
            defMat = SurfaceProperties['default'].getPhysMaterial()
            meshes = self.createConvexPhysMesh()
            shapeDatas = []
            for mesh in meshes:
                shape = PhysShape(mesh, defMat)
                shape.setLocalPos(invOrigin)
                shapeDatas.append((shape, mesh))
            return shapeDatas

        elif self.physType == self.PTTriangles:
            group = self.model.getTriGroup(0)
            triMesh = self.createTrianglePhysMesh()

            materials = []
            for i in range(group.getNumSurfaceProps()):
                materials.append(SurfaceProperties[group.getSurfaceProp(i).lower()].getPhysMaterial())

            shape = PhysShape(triMesh, materials[0])
            shape.setLocalPos(invOrigin)

            # Append remaining materials if there are multiple.
            if len(materials) > 1:
                for i in range(1, len(materials)):
                    shape.addMaterial(materials[i])

            return ((shape, triMesh),)

        return None

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        # Initial transform should be the origin from the solid entity
        # properties.  Vertices are specified in world-space, we need
        # to move them local to the origin.
        self.modelOrigin = self.getTransform()
        self.fetchModel()
        self.parentModelToEntity()

        # 10 = Don't render
        # Hide the model, not the overall entity, because children should
        # show through.
        if self.modelNp and self.renderMode == 10:
            self.modelNp.hide()

    def delete(self):
        self.model = None
        self.modelNp = None
        DistributedEntity.delete(self)

    def parentModelToEntity(self):
        assert self.model
        gn = self.model.getGeomNode()
        if gn:
            np = NodePath(gn)
            np.setTransform(self.modelOrigin.getInverse())
            np.flattenLight()
            np.reparentTo(self)
            self.modelNp = np

    def fetchModel(self):
        self.model = base.game.lvlData.getModel(self.modelNum)
        assert self.model

    def getModelGeomNode(self):
        assert self.model
        return self.model.getGeomNode()

    def createConvexPhysMesh(self):
        meshes = []
        for i in range(self.model.getNumConvexMeshes()):
            meshes.append(PhysConvexMesh(PhysConvexMeshData(self.model.getConvexMeshData(i))))
        return meshes

    def createTrianglePhysMesh(self):
        # NOTE: The world handles multiple collide groups.  Non-world solid
        # entities can only have 1 collide group.
        return PhysTriangleMesh(PhysTriangleMeshData(self.model.getTriGroup(0).getTriMeshData()))

if not IS_CLIENT:
    DistributedSolidEntityAI = DistributedSolidEntity
    DistributedSolidEntityAI.__name__ = 'DistributedSolidEntityAI'

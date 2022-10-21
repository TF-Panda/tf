"""DistributedSolidEntity module: contains the DistributedSolidEntity class."""

from panda3d.core import *
from panda3d.pphysics import *

from .DistributedEntity import DistributedEntity
from tf.tfbase.SurfaceProperties import SurfaceProperties

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
        self.physType = self.PTNone

        self.modelCenter = None

    if not IS_CLIENT:
        def initFromLevel(self, ent, properties):
            DistributedEntity.initFromLevel(self, ent, properties)
            self.modelNum = ent.getModelIndex()

    def makeModelCollisionShape(self):
        if self.modelCenter:
            invCenter = self.modelCenter.getInverse().getPos()
        else:
            invCenter = Point3(0)

        if self.physType == self.PTConvex:
            defMat = SurfaceProperties['default'].getPhysMaterial()
            meshes = self.createConvexPhysMesh()
            shapeDatas = []
            for mesh in meshes:
                shape = PhysShape(mesh, defMat)
                shape.setLocalPos(invCenter)
                shapeDatas.append((shape, mesh))
            return shapeDatas

        elif self.physType == self.PTTriangles:
            triMesh = self.createTrianglePhysMesh()

            materials = []
            for i in range(self.model.getNumSurfaceProps()):
                materials.append(SurfaceProperties[self.model.getSurfaceProp(i).lower()].getPhysMaterial())

            shape = PhysShape(triMesh, materials[0])
            shape.setLocalPos(invCenter)

            # Append remaining materials if there are multiple.
            if len(materials) > 1:
                for i in range(1, len(materials)):
                    shape.addMaterial(materials[i])

            return ((shape, triMesh),)

        return None

    #def generate(self):
        #DistributedEntity.generate(self)
        #self.setPosHpr(0, 0, 0, 0, 0, 0)

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        self.fetchModel()
        self.parentModelToEntity()
        if self.modelCenter:
            self.setTransform(self.modelCenter)
        #self.flattenLight()
        #self.setPosHpr(0, 0, 0, 0, 0, 0)

    def delete(self):
        self.model = None
        DistributedEntity.delete(self)

    def parentModelToEntity(self):
        assert self.model
        gn = self.model.getGeomNode()
        if gn:
            np = NodePath(gn)
            if self.modelCenter:
                np.setTransform(self.modelCenter.getInverse())
                np.flattenLight()
            np.reparentTo(self)

    def fetchModel(self):
        self.model = base.game.lvlData.getModel(self.modelNum)
        assert self.model

        if self.NeedOrigin:
            mins = self.model.getMins()
            maxs = self.model.getMaxs()
            center = maxs + mins
            center *= 0.5
            self.modelCenter = TransformState.makePos(center)

    def getModelGeomNode(self):
        assert self.model
        return self.model.getGeomNode()

    def createConvexPhysMesh(self):
        meshes = []
        for i in range(self.model.getNumConvexMeshes()):
            meshes.append(PhysConvexMesh(PhysConvexMeshData(self.model.getConvexMeshData(i))))
        return meshes

    def createTrianglePhysMesh(self):
        return PhysTriangleMesh(PhysTriangleMeshData(self.model.getTriMeshData()))

if not IS_CLIENT:
    DistributedSolidEntityAI = DistributedSolidEntity
    DistributedSolidEntityAI.__name__ = 'DistributedSolidEntityAI'

"""DistributedSolidEntity module: contains the DistributedSolidEntity class."""

from panda3d.core import *
from panda3d.pphysics import *

from .DistributedEntity import DistributedEntity
from tf.tfbase.SurfaceProperties import SurfaceProperties
from tf.tfbase import TFGlobals

import random

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
        self.modelPos = Point3(0)
        self.modelOrigin = TransformState.makeIdentity()
        self.renderMode = 0

        self.maxDecals = 64
        self.decals = []

    def traceDecal(self, decalName, block, excludeClients=[], client=None):
        if not decalName:
            return
        if IS_CLIENT:
            self.projectDecal(decalName, block.getPosition(), block.getNormal(), random.uniform(0, 360))
        else:
            self.sendUpdate('projectDecal', [decalName, block.getPosition(), block.getNormal(), random.uniform(0, 360)],
                            client=client, excludeClients=excludeClients)

    if not IS_CLIENT:
        def initFromLevel(self, ent, properties):
            DistributedEntity.initFromLevel(self, ent, properties)
            self.modelNum = ent.getModelIndex()
            if properties.hasAttribute("rendermode"):
                self.renderMode = properties.getAttributeValue("rendermode").getInt()

            self.modelOrigin = self.getTransform()
            self.modelPos = self.modelOrigin.getPos()

    else:
        def RecvProxy_modelPos(self, x, y, z):
            self.modelPos = Point3(x, y, z)
            self.modelOrigin = TransformState.makePos(self.modelPos)

        def removeAllDecals(self):
            for decalNp in self.decals:
                decalNp.removeNode()
            self.decals = []

        def removeDecal(self, np):
            np.removeNode()
            self.decals.remove(np)

        def addDecal(self, np):
            np.reparentTo(self)
            self.decals.append(np)

            if len(self.decals) > self.maxDecals:
                self.removeDecal(self.decals[0])

        def projectDecal(self, decalName, position, normal, roll, root=None):
            if not root:
                root = self.modelNp

            if not root or root.isHidden():
                return

            from tf.entity.DecalRegistry import Decals

            from direct.directbase import DirectRender

            info = Decals.get(decalName)
            if not info:
                return

            #print("projecting decal onto", root)

            import random
            matData = random.choice(info['materials'])
            if isinstance(matData, tuple):
                materialFilename, texPos, texSize = matData
            else:
                materialFilename = matData
                texPos = None
                texSize = None
            material = loader.loadMaterial(materialFilename)
            np = NodePath("tmp")
            np.setMaterial(material)
            np.setDepthOffset(1)

            if texPos is not None and texSize is not None:
                tex = material.getParam("base_color").getValue()
                texSizeX = tex.getXSize()
                texSizeY = tex.getYSize()
                # Inverted OpenGL tex coords.
                # Bottom of image is 0 on the Y.
                yPos = texSizeY - texPos[1] - texSize[1]
                uvTransform = TransformState.makePosHprScale((texPos[0] / texSizeX, yPos / texSizeY, 0),
                                                             (0, 0, 0),
                                                             (texSize[0] / texSizeX, texSize[1] / texSizeY, 1))
            else:
                uvTransform = TransformState.makeIdentity()

            q = Quat()
            lookAt(q, normal)
            hpr = q.getHpr()
            hpr[2] = roll

            size = info['size']

            proj = DecalProjector()
            proj.setProjectorParent(base.render)
            proj.setProjectorTransform(TransformState.makePosHpr(position, hpr))
            proj.setProjectorBounds(-size * 0.5, size * 0.5)
            proj.setDecalParent(self)
            proj.setDecalRenderState(np.getState())
            proj.setDecalUvTransform(uvTransform)
            if proj.project(root):
                decalNp = NodePath(proj.generate())
                decalNp.hide(DirectRender.ShadowCameraBitmask)
                decalNp.hide(DirectRender.ReflectionCameraBitmask)
                self.addDecal(decalNp)

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
        #self.modelOrigin = self.getTransform()
        self.fetchModel()
        self.parentModelToEntity()

        # 10 = Don't render
        # Hide the model, not the overall entity, because children should
        # show through.
        if self.modelNp and self.renderMode == 10:
            self.modelNp.hide()

    def delete(self):
        if IS_CLIENT:
            self.removeAllDecals()
            self.decals = None
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

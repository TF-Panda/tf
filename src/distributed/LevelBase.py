"""LevelBase module: contains the LevelBase class."""

from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase.TFGlobals import Contents

class LevelBase:
    """
    Implements shared functionality between client and AI for loading levels.
    Decoupled from distributed system to allow loading levels in standalone
    programs.
    """

    def __init__(self):
        self.lvl = None
        self.lvlData = None

    def unloadLevel(self):
        if self.lvl:
            self.lvl.removeNode()
            self.lvl = None
        self.lvlData = None
        self.levelName = None

    def loadLevel(self, lvlName):
        self.unloadLevel()

        self.lvl = loader.loadModel(lvlName)
        self.lvl.reparentTo(base.render)
        lvlRoot = self.lvl.find("**/+MapRoot")
        lvlRoot.setLightOff(1)
        # Make sure all the RAM copies of lightmaps get thrown away when they
        # get uploaded to the graphics card.  They take up a lot of memory.
        for tex in lvlRoot.findAllTextures():
            tex.setKeepRamImage(False)
        data = lvlRoot.node().getData()
        self.lvlData = data

        for gnp in self.lvl.findAllMatches("**/+GeomNode"):
            gnp.node().setFinal(True)

        for i in range(data.getNumModelPhysDatas()):
            meshBuffer = data.getModelPhysData(i)
            if len(meshBuffer) == 0:
                continue
            meshData = PhysTriangleMeshData(meshBuffer)
            geom = PhysTriangleMesh(meshData)
            shape = PhysShape(geom, PhysMaterial(0.4, 0.25, 0.2))
            body = PhysRigidStaticNode("model-phys-%i" % i)
            body.addShape(shape)
            body.setFromCollideMask(Contents.Solid)
            body.addToScene(base.physicsWorld)
            body.setPythonTag("entity", base.world)
            body.setPythonTag("object", base.world)
            self.lvl.attachNewNode(body)

        self.loadLevelProps()

    def loadLevelProps(self):
        # Create a dedicated DynamicVisNode for culling static props.
        # We have one node dedicated to culling static props and another
        # for dynamic entities (which is base.dynRender).  The reason for
        # this is to reduce the overhead of recomputing the bounding volume
        # of base.dynRender.  If static props and dynamic entities are
        # parented to the same node, we have a lot more nodes to union.
        # And since static props never move, that would be a waste.
        propRoot = self.lvl.attachNewNode(DynamicVisNode("props"))
        propRoot.node().levelInit(self.lvlData.getNumClusters())
        for i in range(self.lvlData.getNumEntities()):
            ent = self.lvlData.getEntity(i)
            if ent.getClassName() != "prop_static":
                continue

            props = ent.getProperties()

            modelFilename = Filename.fromOsSpecific(props.getAttributeValue("model").getString().replace(".mdl", ".bam"))
            propModel = loader.loadModel(modelFilename, okMissing=True)
            if not propModel or propModel.isEmpty():
                continue

            if props.hasAttribute("skin"):
                skin = props.getAttributeValue("skin").getInt()
                if skin >= 0 and skin < propModel.node().getNumMaterialGroups():
                    propModel.node().setActiveMaterialGroup(skin)

            if props.hasAttribute("origin"):
                pos = Point3()
                props.getAttributeValue("origin").toVec3(pos)
                propModel.setPos(pos)

            if props.hasAttribute("angles"):
                phr = Vec3()
                props.getAttributeValue("angles").toVec3(phr)
                propModel.setHpr(phr[1] - 90, -phr[0], phr[2])

            cnode = None
            cinfo = propModel.node().getCollisionInfo()
            if props.getAttributeValue("solid").getInt() != 0 and cinfo and cinfo.getPart(0).mesh_data:
                part = cinfo.getPart(0)
                if part.concave:
                    mdata = PhysTriangleMeshData(part.mesh_data)
                else:
                    mdata = PhysConvexMeshData(part.mesh_data)
                if mdata.generateMesh():
                    if part.concave:
                        mesh = PhysTriangleMesh(mdata)
                    else:
                        mesh = PhysConvexMesh(mdata)
                    mat = PhysMaterial(0.5, 0.5, 0.5)
                    shape = PhysShape(mesh, mat)
                    cnode = PhysRigidStaticNode("propcoll")
                    cnode.addShape(shape)
                    cnode.addToScene(base.physicsWorld)
                    cnp = propModel.attachNewNode(cnode)
                    cnp.setTransform(NodePath(), propModel.getTransform(NodePath()))
                    cnode.setFromCollideMask(Contents.Solid)
                    cnode.setPythonTag("entity", base.world)
                    cnode.setPythonTag("object", base.world)

            propModel.reparentTo(propRoot)
            propModel.flattenStrong()
            propModel.node().setFinal(True)
            # Static props don't have precomputed lighting yet, so treat them
            # as dynamic models for lighting purposes.
            propModel.setEffect(MapLightingEffect.make())
            if cnode:
                cnode.syncTransform()

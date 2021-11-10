
from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase.TFGlobals import Contents

class DistributedGameBase:

    def __init__(self):
        self.levelName = ""
        self.lvl = None
        self.lvlData = None

    def loadLevelProps(self):
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
                    cnode.setContentsMask(Contents.Solid)
                    cnode.setPythonTag("entity", base.world)

            propModel.reparentTo(self.lvl)
            propModel.flattenStrong()
            propModel.node().setFinal(True)

    def delete(self):
        if self.lvl:
            self.lvl.removeNode()
            self.lvl = None
        self.lvlData = None
        self.levelName = None

    def changeLevel(self, lvlName):
        self.levelName = lvlName

        if self.lvl:
            self.lvl.removeNode()

        self.lvl = loader.loadModel(lvlName)
        self.lvl.reparentTo(base.render)
        lvlRoot = self.lvl.find("**/+MapRoot")
        lvlRoot.setLightOff(1)
        data = lvlRoot.node().getData()
        self.lvlData = data

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
            body.setPythonTag("entity", base.world)
            self.lvl.attachNewNode(body)

        self.loadLevelProps()

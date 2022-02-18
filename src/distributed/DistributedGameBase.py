
from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase.TFGlobals import Contents
from tf.tfbase.SurfaceProperties import SurfaceProperties

from direct.directbase import DirectRender

class DistributedGameBase:

    def __init__(self):
        self.levelName = ""
        self.lvl = None
        self.lvlData = None
        self.propPhysRoot = None

    def loadLevelProps(self):
        # Create a dedicated DynamicVisNode for culling static props.
        # We have one node dedicated to culling static props and another
        # for dynamic entities (which is base.dynRender).  The reason for
        # this is to reduce the overhead of recomputing the bounding volume
        # of base.dynRender.  If static props and dynamic entities are
        # parented to the same node, we have a lot more nodes to union.
        # And since static props never move, that would be a waste.
        propRoot = self.lvl.attachNewNode(DynamicVisNode("props"))
        propPhysRoot = NodePath("propPhysRoot")
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

                    surfaceProp = "default"
                    cdata = propModel.node().getCustomData()
                    if cdata:
                        if cdata.hasAttribute("surfaceprop"):
                            surfaceProp = cdata.getAttributeValue("surfaceprop").getString().lower()
                    mat = SurfaceProperties[surfaceProp].getPhysMaterial()

                    shape = PhysShape(mesh, mat)
                    cnode = PhysRigidStaticNode("propcoll")
                    cnode.addShape(shape)
                    cnode.addToScene(base.physicsWorld)
                    cnp = propPhysRoot.attachNewNode(cnode)
                    cnp.setTransform(NodePath(), propModel.getTransform(NodePath()))
                    cnode.setContentsMask(Contents.Solid)
                    cnode.setPythonTag("entity", base.world)

            propModel.reparentTo(propRoot)
            propModel.clearModelNodes()
            propModel.flattenStrong()
            #lodNode = propModel.find("**/+LODNode")
            #if not lodNode.isEmpty():
                # Grab the first LOD and throw away the rest so we can flatten.
            #    highestLod = lodNode.getChild(0)
            #    highestLod.reparentTo(lodNode.getParent())
            #    lodNode.removeNode()
            propModel.node().setFinal(True)
            propModel.showThrough(DirectRender.ShadowCameraBitmask)
            # Static props don't have precomputed lighting yet, so treat them
            # as dynamic models for lighting purposes.
            propModel.setEffect(MapLightingEffect.make())
            if cnode:
                cnode.syncTransform()

        self.propPhysRoot = propPhysRoot

    def delete(self):
        self.unloadLevel()

    def unloadLevel(self):
        if self.lvl:
            self.lvl.removeNode()
            self.lvl = None
        self.lvlData = None
        self.levelName = None

    def changeLevel(self, lvlName):
        self.unloadLevel()

        self.levelName = lvlName

        self.lvl = loader.loadModel(lvlName)
        self.lvl.reparentTo(base.render)
        lvlRoot = self.lvl.find("**/+MapRoot")
        lvlRoot.setLightOff(-1)
        self.lvl.showThrough(DirectRender.ShadowCameraBitmask)
        # Make sure all the RAM copies of lightmaps get thrown away when they
        # get uploaded to the graphics card.  They take up a lot of memory.
        for tex in lvlRoot.findAllTextures():
            tex.setKeepRamImage(False)
        data = lvlRoot.node().getData()
        self.lvlData = data

        dummyRoot = PandaNode("mapRoot")
        dummyRoot.replaceNode(lvlRoot.node())

        for gnp in self.lvl.findAllMatches("**/+GeomNode"):
            #gnp.node().setFinal(True)

            # Delete skybox faces so we can do the actual source engine
            # skybox rendering.
            for i in reversed(range(gnp.node().getNumGeoms())):
                geom = gnp.node().getGeom(i)
                state = gnp.node().getGeomState(i)
                if state.hasAttrib(MaterialAttrib):
                    mattr = state.getAttrib(MaterialAttrib)
                    mat = mattr.getMaterial()
                    if mat and isinstance(mat, SkyBoxMaterial):
                        gnp.node().removeGeom(i)

        self.lvl.clearModelNodes()
        self.lvl.flattenStrong()

        self.loadLevelProps()

        physRoot = self.lvl.attachNewNode("physRoot")
        for i in range(data.getNumModelPhysDatas()):
            mapModelPhysData = data.getModelPhysData(i)
            meshBuffer = mapModelPhysData._phys_mesh_data
            if len(meshBuffer) == 0:
                continue
            meshData = PhysTriangleMeshData(meshBuffer)
            geom = PhysTriangleMesh(meshData)

            materials = []
            for j in range(mapModelPhysData.getNumSurfaceProps()):
                materials.append(SurfaceProperties[mapModelPhysData.getSurfaceProp(j).lower()].getPhysMaterial())

            shape = PhysShape(geom, materials[0])

            # Append remaining materials if there are multiple.
            if len(materials) > 1:
                for j in range(1, len(materials)):
                    shape.addMaterial(materials[j])

            body = PhysRigidStaticNode("model-phys-%i" % i)
            body.addShape(shape)
            body.setContentsMask(Contents.Solid)
            body.addToScene(base.physicsWorld)
            body.setPythonTag("entity", base.world)
            physRoot.attachNewNode(body)
        self.propPhysRoot.reparentTo(self.lvl)

        self.lvl.ls()
        self.lvl.analyze()

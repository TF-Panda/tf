
from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase.TFGlobals import Contents
from tf.tfbase.SurfaceProperties import SurfaceProperties

from direct.directbase import DirectRender

from .GameMode import GameMode

class DistributedGameBase:

    def __init__(self):
        self.levelName = ""
        self.lvl = None
        self.lvlData = None
        self.propRoot = None
        self.propPhysRoot = None
        self.gameMode = GameMode.Arena

    def flatten(self, np):
        # Does a flatten even stronger than NodePath.flattenStrong()
        gr = SceneGraphReducer()
        gr.applyAttribs(np.node())
        gr.flatten(np.node(), ~0)
        gr.makeCompatibleState(np.node())
        gr.collectVertexData(np.node(), 0)
        gr.unify(np.node(), False)

    def loadLevelProps(self):
        # Create a dedicated DynamicVisNode for culling static props.
        # We have one node dedicated to culling static props and another
        # for dynamic entities (which is base.dynRender).  The reason for
        # this is to reduce the overhead of recomputing the bounding volume
        # of base.dynRender.  If static props and dynamic entities are
        # parented to the same node, we have a lot more nodes to union.
        # And since static props never move, that would be a waste.

        tree = self.lvlData.getAreaClusterTree()

        propRoot = base.render.attachNewNode(StaticPartitionedObjectNode("props"))
        self.propRoot = propRoot
        propRoot.showThrough(DirectRender.ShadowCameraBitmask)
        propPhysRoot = NodePath("propPhysRoot")
        propPhysRoot.hide()
        lightNodes = []
        for i in range(self.lvlData.getNumEntities()):
            ent = self.lvlData.getEntity(i)
            if ent.getClassName() != "prop_static":
                continue

            props = ent.getProperties()

            if not props.hasAttribute("model"):
                continue

            modelVal = props.getAttributeValue("model")
            if not modelVal.isString():
                continue

            modelFilename = Filename.fromOsSpecific(modelVal.getString().replace(".mdl", ".bam"))
            propModel = loader.loadModel(modelFilename, okMissing=True)
            if not propModel or propModel.isEmpty():
                continue

            if props.hasAttribute("skin"):
                skin = props.getAttributeValue("skin").getInt()
                if skin >= 0 and skin < propModel.node().getNumMaterialGroups():
                    propModel.node().setActiveMaterialGroup(skin)

            pos = Point3()
            if props.hasAttribute("origin"):
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
                    sp = SurfaceProperties.get(surfaceProp)
                    if not sp:
                        sp = SurfaceProperties['default']
                    mat = sp.getPhysMaterial()

                    shape = PhysShape(mesh, mat)
                    cnode = PhysRigidStaticNode("propcoll")
                    cnode.addShape(shape)
                    cnode.addToScene(base.physicsWorld)
                    cnp = propPhysRoot.attachNewNode(cnode)
                    cnp.setTransform(NodePath(), propModel.getTransform(NodePath()))
                    cnode.setContentsMask(Contents.Solid)
                    #cnode.setPythonTag("entity", base.world)

            propModel.flattenStrong()
            lodNode = propModel.find("**/+LODNode")
            if not lodNode.isEmpty():
                # Grab the first LOD and throw away the rest so we can flatten.
                propModel = lodNode.getChild(0)

            propModel.flattenStrong()

            if propModel.getNumChildren() == 1:
                # If there's just one GeomNode under the ModelRoot, we can throw
                # away the model root.
                propModel = propModel.getChild(0)

            propModel.reparentTo(propRoot)
            in3DSky = False
            if IS_CLIENT:
                # If the prop is positioned in the 3-D skybox, it needs to be
                # parented into the 3-D skybox scene graph.
                leaf = tree.getLeafValueFromPoint(pos)
                if leaf >= 0:
                    pvs = self.lvlData.getClusterPvs(leaf)
                    if pvs.is3dSkyCluster():
                        propModel.reparentTo(base.sky3DRoot)
                        in3DSky = True

                propModel.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
                lightNodes.append(propModel)

            propModel.node().setFinal(True)
            if not in3DSky:
                propModel.showThrough(DirectRender.ShadowCameraBitmask)

            if cnode:
                cnode.syncTransform()

        self.flatten(propRoot)

        for propModel in lightNodes:
            # Also, we can flatten better by pre-computing the lighting state once.
            lightEffect = propModel.getEffect(MapLightingEffect.getClassType())
            lightEffect.computeLighting(propModel.getNetTransform(), self.lvlData,
                                        propModel.getBounds(), propModel.getParent().getNetTransform())
            state = propModel.getState()
            state = state.compose(lightEffect.getCurrentLightingState())
            propModel.setState(state)
            propModel.clearEffect(MapLightingEffect.getClassType())
            propModel.flattenLight()

        for child in propRoot.getChildren():
            propRoot.node().addObject(child.node())
        propRoot.node().removeAllChildren()

        propRoot.node().partitionObjects(self.lvlData.getNumClusters(), self.lvlData.getAreaClusterTree())

        self.propPhysRoot = propPhysRoot

    def delete(self):
        self.unloadLevel()

    def unloadLevel(self):
        if self.propRoot:
            self.propRoot.removeNode()
            self.propRoot = None
        if self.lvl:
            self.lvl.removeNode()
            self.lvl = None
        self.lvlData = None
        self.levelName = None

    def preFlattenLevel(self):
        pass

    def changeLevel(self, lvlName):
        self.unloadLevel()

        self.levelName = lvlName

        self.lvl = loader.loadModel(lvlName)
        #self.lvl.reparentTo(base.render)
        lvlRoot = self.lvl.find("**/+MapRoot")
        lvlRoot.setLightOff(-1)
        data = lvlRoot.node().getData()
        self.lvlData = data

        # Make sure all the RAM copies of lightmaps and cube maps get thrown away when they
        # get uploaded to the graphics card.  They take up a lot of memory.
        for tex in self.lvl.findAllTextures():
            tex.setKeepRamImage(False)
        for i in range(self.lvlData.getNumCubeMaps()):
            mcm = self.lvlData.getCubeMap(i)
            tex = mcm.getTexture()
            if tex:
                tex.setKeepRamImage(False)
                tex.setMinfilter(SamplerState.FTLinear)
                tex.setMagfilter(SamplerState.FTLinear)
                tex.clearRamMipmapImages()

        dummyRoot = PandaNode("mapRoot")
        dummyRoot.replaceNode(lvlRoot.node())

        for i in range(self.lvlData.getNumModels()):
            mdl = self.lvlData.getModel(i)
            gn = mdl.getGeomNode()
            for i in reversed(range(gn.getNumGeoms())):
                geom = gn.getGeom(i)
                state = gn.getGeomState(i)
                if state.hasAttrib(MaterialAttrib):
                    mattr = state.getAttrib(MaterialAttrib)
                    mat = mattr.getMaterial()
                    if mat and isinstance(mat, SkyBoxMaterial):
                        gn.removeGeom(i)

        self.preFlattenLevel()

        self.loadLevelProps()

        self.propPhysRoot.reparentTo(self.lvl)

        #self.lvl.ls()

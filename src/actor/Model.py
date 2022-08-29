"""Model module: contains the Model class."""

from panda3d.core import *
from panda3d.pphysics import *

from tf.tfbase.SurfaceProperties import SurfaceProperties

from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify

class Model(DirectObject):
    """
    Encapsulation of a model in the scene graph.  This is the base class
    for Actor.  Static models can just use the Model class, but animated
    characters need to use the Actor class.
    """

    notify = directNotify.newCategory("Model")

    def __init__(self):
        # NodePath of ModelRoot, the top level node in the loaded model.
        self.modelNp = None
        self.modelRootNode = None
        self.modelNode = None
        self.modelData = None
        self.model = ""
        # Current model material group/skin.  Saved here so if we change
        # models the active skin is carried over to the new model.
        self.skin = 0
        self.bodygroups = {}

    def setSkin(self, skin):
        """
        Sets the active material group of the actor to the specified index.
        """
        if skin != self.skin or (self.modelRootNode and self.modelRootNode.getActiveMaterialGroup() != skin):
            self.skin = skin
            self.updateSkin()

    def updateSkin(self):
        """
        Updates the model to use the currently specified material group/skin.
        """
        if self.modelRootNode:
            if self.skin >= 0 and self.skin < self.modelRootNode.getNumMaterialGroups():
                self.modelRootNode.setActiveMaterialGroup(self.skin)

    def cleanup(self):
        self.unloadModel()
        self.bodygroups = None
        self.skin = None
        self.model = None

    def unloadModel(self):
        """
        Removes the current model from the scene graph and all related data.
        """
        if self.modelNp:
            self.modelNp.removeNode()
            self.modelNp = None
        self.modelNode = None
        self.modelRootNode = None
        self.modelData = None
        self.model = ""
        self.bodygroups = {}

    def loadBodygroups(self):
        """
        Loads up the bodygroup information from the model's "custom data"
        structure.  Bodygroups in this context are collections of nodes
        that can be toggled on and off through game code and animations.

        Most of the time a bodygroup contains the nodes pertaining to a
        piece of the model at all LOD levels.  For instance, a "rocket"
        bodygroup contains all of the "rocket" prefixed nodes under each
        LODNode of the model.
        """

        data = self.modelData
        if not data:
            return
        if not data.hasAttribute("bodygroups"):
            return
        bgs = data.getAttributeValue("bodygroups").getList()
        for i in range(len(bgs)):
            bgdata = bgs.get(i).getElement()
            name = bgdata.getAttributeValue("name").getString()
            self.bodygroups[name] = []
            nodes = bgdata.getAttributeValue("nodes").getList()
            for j in range(len(nodes)):
                pattern = nodes.get(j).getString()
                if pattern == "blank":
                    self.bodygroups[name].append(NodePathCollection())
                else:
                    self.bodygroups[name].append(
                        self.modelNp.findAllMatches("**/" + pattern))

        # Default every bodygroup to the 0 index.
        for name in self.bodygroups.keys():
            self.setBodygroupValue(name, 0)

    def setBodygroupValue(self, group, value):
        """
        Sets the value of the bodygroup with the indicated name.
        The node collection at the index of the given value is shown,
        while all other collections in the bodygroup are hidden.
        """
        bg = self.bodygroups.get(group, [])
        for i in range(len(bg)):
            body = bg[i]
            if i == value:
                body.show()
            else:
                body.hide()

    def getBodygroupNodes(self, group, value):
        """
        Returns the set of NodePaths that are turned on by the given bodygroup
        value.
        """

        bg = self.bodygroups.get(group)
        if not bg:
            return NodePathCollection()

        if value < 0 or value >= len(bg):
            return NodePathCollection()

        return bg[value]

    def resetBodygroup(self, group):
        """
        Resets the bodygroup with the indicated name to the default variant.
        """
        self.setBodygroupValue(group, 0)

    def resetBodygroups(self):
        """
        Resets all bodygroups to their defaults.
        """
        for bg in self.bodygroups.values():
            bg[0].show()
            for i in range(1, len(bg)):
                bg[i].hide()

    def getModelSurfaceProp(self):
        surfaceProp = "default"
        data = self.modelData
        if data:
            if data.hasAttribute("surfaceprop"):
                surfaceProp = data.getAttributeValue("surfaceprop").getString().lower()
        return surfaceProp

    def makeModelCollisionShape(self):
        cinfo = self.modelRootNode.getCollisionInfo()
        if not cinfo:
            return None
        part = cinfo.getPart(0)

        surfaceProp = self.getModelSurfaceProp()

        if part.concave:
            mdata = PhysTriangleMeshData(part.mesh_data)
        else:
            mdata = PhysConvexMeshData(part.mesh_data)
        if not mdata.generateMesh():
            return None
        if part.concave:
            mesh = PhysTriangleMesh(mdata)
        else:
            mesh = PhysConvexMesh(mdata)
        mat = SurfaceProperties[surfaceProp].getPhysMaterial()
        shape = PhysShape(mesh, mat)
        return ((shape, mesh),)

    def onModelChanged(self):
        """
        Called when a new model has been loaded.
        """
        pass

    def loadModel(self, filename):
        """
        Loads up a model from the indicated model filename.  The existing
        model is unloaded.

        Returns true if the model was loaded successfully, false otherwise.
        """

        if self.model == filename:
            return False

        # Different model, unload existing.
        self.unloadModel()

        self.model = filename

        if len(filename) == 0:
            # No model.
            return False

        self.modelNp = base.loader.loadModel(filename, okMissing=True)
        if not self.modelNp or self.modelNp.isEmpty():
            self.notify.error("Could not load model %s" % filename)
            return False
        self.modelRootNode = self.modelNp.node()
        if self.modelNp.find("**/+CharacterNode").isEmpty():
            # Not a character, so flatten it out.
            self.modelNp.flattenStrong()
        if self.modelNp.getNumChildren() == 1:
            # Get rid of the ModelRoot node.
            # We need to instance the child so the ModelRoot is still a parent
            # of the child and can properly change material groups.
            self.modelNp = self.modelNp.getChild(0).instanceTo(NodePath())
            self.modelNode = self.modelNp.node()
        else:
            self.modelNode = self.modelRootNode
        # Cull the model's subgraph as a single unit.
        #self.modelNode.setFinal(True)
        self.modelData = self.modelRootNode.getCustomData()

        modelNode = self.modelNode
        modelNode.setFinal(True)
        cdata = self.modelData
        if cdata:
            if cdata.hasAttribute("omni") and cdata.getAttributeValue("omni").getBool():
                modelNode.setBounds(OmniBoundingVolume())
            if cdata.hasAttribute("bbox"):
                # Model specifies a user bounding volume.
                # Note that this doesn't override the bounds of the geometry
                # of the model, it just unions with it.
                mins = Point3()
                maxs = Point3()
                bbox = cdata.getAttributeValue("bbox").getElement()
                bbox.getAttributeValue("mins").toVec3(mins)
                bbox.getAttributeValue("maxs").toVec3(maxs)
                modelNode.setBounds(BoundingBox(mins, maxs))

        # Collect all bodygroups and toggle the default ones.
        self.loadBodygroups()

        # Apply the currently specified skin.
        self.updateSkin()

        self.onModelChanged()

        return True

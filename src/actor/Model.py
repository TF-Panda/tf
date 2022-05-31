"""Model module: contains the Model class."""

from panda3d.core import NodePathCollection

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
        self.modelNode = None
        # Current model material group/skin.  Saved here so if we change
        # models the active skin is carried over to the new model.
        self.skin = 0
        self.bodygroups = {}

    def setSkin(self, skin):
        """
        Sets the active material group of the actor to the specified index.
        """
        self.skin = skin
        self.updateSkin()

    def updateSkin(self):
        """
        Updates the model to use the currently specified material group/skin.
        """
        if self.modelNode:
            if self.skin >= 0 and self.skin < self.modelNode.getNumMaterialGroups():
                self.modelNode.setActiveMaterialGroup(self.skin)

    def unloadModel(self):
        """
        Removes the current model from the scene graph and all related data.
        """
        if self.modelNp:
            self.modelNp.removeNode()
            self.modelNp = None
        self.modelNode = None
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
        if not self.modelNode:
            return

        data = self.modelNode.getCustomData()
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

    def loadModel(self, filename):
        """
        Loads up a model from the indicated model filename.  The existing
        model is unloaded.

        Returns true if the model was loaded successfully, false otherwise.
        """

        self.unloadModel()

        self.modelNp = base.loader.loadModel(filename)
        if not self.modelNp or self.modelNp.isEmpty():
            self.notify.error("Could not load model %s" % filename)
            return False
        self.modelNode = self.modelNp.node()
        # Cull the model's subgraph as a single unit.
        self.modelNode.setFinal(True)

        # Collect all bodygroups and toggle the default ones.
        self.loadBodygroups()

        # Apply the currently specified skin.
        self.updateSkin()

        return True

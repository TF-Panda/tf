
if IS_CLIENT:
    from direct.distributed2.DistributedObject import DistributedObject
    BaseClass = DistributedObject
else:
    from direct.distributed2.DistributedObjectAI import DistributedObjectAI
    BaseClass = DistributedObjectAI

from panda3d.core import NodePath, Point3, Vec3
from panda3d.direct import InterpolatedVec3

from tf.tfbase.TFGlobals import WorldParent, getWorldParent

class DistributedEntity(BaseClass, NodePath):

    def __init__(self):
        BaseClass.__init__(self)
        NodePath.__init__(self, "entity")

        # The team affiliation of the entity.  This is where a pluggable
        # component system would come in handy.  We could allow entities/DOs
        # to contain components that add new data/functionality onto an
        # entity that needs it, without having to modify the base class for
        # all entities.
        self.team = -1

        # Another thing that could be done with components.  Surely, not all
        # entities need health.
        self.health = 0
        self.maxHealth = 0

        # DoId of our parent entity, or world parent code.  >= 0 is a parent
        # entity doId, < 0 is a world parent code.  A world parent is a scene
        # node instead of an entity (like render or camera).
        self.parentEntityId = -1
        # Handle to the actual parent entity or node.
        self.parentEntity = base.hidden

        if IS_CLIENT:
            # Add interpolators for transform state of the entity/node.
            self.ivPos = InterpolatedVec3()
            self.addInterpolatedVar(self.ivPos, self.getPos, self.setPos)
            self.ivHpr = InterpolatedVec3()
            self.addInterpolatedVar(self.ivHpr, self.getHpr, self.setHpr)
            self.ivScale = InterpolatedVec3()
            #self.addInterpolatedVar(self.ivScale, self.getScale, self.setScale)

        # Create a root node for all physics objects to live under, and hide
        # it.  This can improve cull traverser performance since it only has
        # to consider visiting the root node instead of every individual
        # physics node.
        self.physicsRoot = self.attachNewNode("physics")
        self.physicsRoot.node().setOverallHidden(True)
        self.physicsRoot.node().setFinal(True)

        # Add a tag on our node that links back to us.
        self.setPythonTag("entity", self)

        self.reparentTo(self.parentEntity)

    def getPhysicsRoot(self):
        """
        Returns the physics root node of the entity; the node that all physics
        nodes live under.
        """
        return self.physicsRoot

    def getParentEntity(self):
        return self.parentEntity

    def getParentEntityId(self):
        return self.parentEntityId

    def getHealth(self):
        return self.health

    def getMaxHealth(self):
        return self.maxHealth

    def getTeam(self):
        return self.team

    def parentChanged(self):
        """
        Called when the parent of the entity has changed.
        """
        pass

    def setParentEntityId(self, parentId):
        """
        Sets the parent of this entity.  Parent is referred to by doId.  Can
        also be a world parent code, in which case the entity will be parented
        to the associated scene graph node instead of an entity.
        """

        if parentId != self.parentEntityId:
            if parentId < 0:
                # It's a world parent.
                parentNode = getWorldParent(parentId)
                # If the world parent is None, don't change the current
                # parent.
                if parentNode is not None:
                    self.reparentTo(parentNode)
                self.parentEntity = parentNode
            else:
                # Should be an entity parent.
                parentEntity = base.net.doId2do.get(parentId)
                if parentEntity is not None:
                    self.reparentTo(parentEntity)
                else:
                    # If parent entity not found, parent to hidden.  Better
                    # idea than parenting to render and having the model
                    # just float in space or something.
                    self.reparentTo(base.hidden)
                self.parentEntity = parentEntity
            self.parentChanged()
        self.parentEntityId = parentId

    if IS_CLIENT:
        ###########################################################################
        # These receive proxies apply the received transforms directly to our
        # node.

        def RecvProxy_pos(self, x, y, z):
            self.setPos((x, y, z))

        def RecvProxy_hpr(self, h, p, r):
            self.setHpr((h, p, r))

        def RecvProxy_scale(self, x, y, z):
            self.setScale((x, y, z))

        def RecvProxy_parentEntityId(self, parentId):
            # If the parent changed, reset our transform interp vars.
            if parentId != self.parentEntityId:
                self.ivPos.reset(self.getPos())
                self.ivHpr.reset(self.getHpr())
                self.ivScale.reset(self.getScale())
                self.setParentEntity(parentId)

        ###########################################################################
    else: # SERVER

        def SendProxy_pos(self):
            return self.getPos()

        def SendProxy_hpr(self):
            return self.getHpr()

        def SendProxy_scale(self):
            return self.getScale()

    def delete(self):
        if IS_CLIENT:
            self.ivPos = None
            self.ivHpr = None
            self.ivScale = None
        self.parentEntity = None
        self.physicsRoot = None
        # Release the root node of the entity.
        self.removeNode()
        BaseClass.delete(self)

if not IS_CLIENT:
    DistributedEntityAI = DistributedEntity

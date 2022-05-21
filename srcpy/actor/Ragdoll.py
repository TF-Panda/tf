from panda3d.pphysics import *
from panda3d.core import *

from tf.tfbase.SurfaceProperties import SurfaceProperties

class Ragdoll(PhysRagdoll):

    def __init__(self, characterNp, collInfo):
        PhysRagdoll.__init__(self, characterNp)
        #self.setDebug(True, 4.0)
        self.task = None
        self.collInfo = collInfo
        self.characterNp = characterNp
        self.characterNp.node().setFinal(True)

    def getRagdollPosition(self):
        return Point3(self.getJointActor(self.collInfo.root_part).getTransform().getPos())

    def getRagdollMatrix(self):
        # Returns the world-space matrix transform of the root ragdoll joint.
        return self.getJointActor(self.collInfo.root_part).getTransform().getMat()

    def setup(self):
        #collideWith = {}
        for i in range(self.collInfo.getNumParts()):
            part = self.collInfo.getPart(i)
            meshData = PhysConvexMeshData(part.mesh_data)
            mesh = PhysConvexMesh(meshData)
            shape = PhysShape(mesh, SurfaceProperties['flesh'].getPhysMaterial())
            if part.parent != -1:
                parentName = self.collInfo.getPart(part.parent).name
            else:
                parentName = ""
            self.addJoint(parentName, part.name, shape, part.mass, part.rot_damping * 10,
                          part.damping, part.limit_x, part.limit_y, part.limit_z)

    def __update(self, task):
        self.update()

        # Recompute a bounding volume that contains all of the ragdoll's joint positions.
        # FIXME: This isn't a perfect solution.  The ragdoll bounds will be unioned
        # with the bounds of the character geometry, which will be stationed at the ragdoll's
        # initial position.  This means the character's bounding volume will stretch in the
        # direction that the ragdoll moves.  A better solution would be to do the unioning
        # of the ragdoll limb bounds, but also move the root of the character node to the
        # position of the root ragdoll joint.  That means we also have to change how the
        # joint transforms are computed.
        bounds = BoundingBox()
        for i in range(self.getNumJoints()):
            actorBounds = self.getJointActor(i).getPhysBounds()
            # It's currently in world-space.  Transform it to be relative to
            # the character.
            actorBounds.xform(self.characterNp.getNetTransform().getInverse().getMat())
            bounds.extendBy(actorBounds)

        self.characterNp.node().setBounds(bounds)

        return task.cont

    def destroy(self):
        if self.task:
            self.task.remove()
        self.task = None
        self.characterNp = None
        PhysRagdoll.destroy(self)

    def setEnabled(self, enable, forceJointName, forceVector, forcePos):
        if enable:
            self.startRagdoll(base.physicsWorld, base.dynRender)
            if self.task:
                self.task.remove()
            self.task = base.taskMgr.add(self.__update, 'ragdollUpdate', sort = 35)

            if forceJointName is not None:
                forceJoint = self.getJointActor(forceJointName)
            else:
                forceJoint = self.getJointActor(self.collInfo.root_part)

            if (forceVector.lengthSquared() > 0.001):

                forceJoint.addForce(forceVector, forceJoint.FTImpulse)
                forcePos = Point3(forceJoint.getTransform().getPos())


                if forcePos != Point3(0):
                    for i in range(self.getNumJoints()):
                        joint = self.getJointActor(i)
                        if joint == forceJoint:
                            continue
                        scale = joint.getMass() / self.collInfo.total_mass
                        joint.addForceAtPos(forceVector * scale, forcePos, joint.FTImpulse)
        else:
            self.stopRagdoll()
            if self.task:
                self.task.remove()
                self.task = None

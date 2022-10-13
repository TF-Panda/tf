from panda3d.pphysics import *
from panda3d.core import *

from tf.tfbase.SurfaceProperties import SurfaceProperties
from tf.tfbase.TFGlobals import CollisionGroup

class Ragdoll(PhysRagdoll):

    def __init__(self, characterNp, collInfo):
        PhysRagdoll.__init__(self, characterNp)
        #self.setDebug(True, 4.0)
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
            self.addJoint(parentName, part.name, shape, part.mass, part.rot_damping,
                          part.damping, part.inertia, part.limit_x, part.limit_y, part.limit_z)

    def destroy(self):
        self.characterNp = None
        PhysRagdoll.destroy(self)

    def setEnabled(self, enable, forceJointName, forceVector, forcePos, initialVel = Vec3(0)):
        if enable:
            self.startRagdoll(base.physicsWorld, base.dynRender)

            for i in range(self.getNumJoints()):
                actor = self.getJointActor(i)
                actor.setCollisionGroup(CollisionGroup.Debris)
                actor.setPythonTag("object", self)

            initialVel = Vec3(initialVel[0], initialVel[1], initialVel[2])
            if initialVel.lengthSquared() > 0.001:
                for i in range(self.getNumJoints()):
                    joint = self.getJointActor(i)
                    joint.addForce(initialVel, joint.FTVelocityChange)

            if (forceVector.lengthSquared() > 0.001):
                if forceJointName is not None:
                    forceJoint = self.getJointActor(forceJointName)
                else:
                    forceJoint = self.getJointActor(self.collInfo.root_part)

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

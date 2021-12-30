from panda3d.pphysics import *
from panda3d.core import *

HardSounds = [
    "sound/physics/body/body_medium_impact_hard1.wav",
    "sound/physics/body/body_medium_impact_hard2.wav",
    "sound/physics/body/body_medium_impact_hard3.wav",
    "sound/physics/body/body_medium_impact_hard4.wav",
    "sound/physics/body/body_medium_impact_hard5.wav",
    "sound/physics/body/body_medium_impact_hard6.wav"
]
SoftSounds = [
    "sound/physics/body/body_medium_impact_soft1.wav",
    "sound/physics/body/body_medium_impact_soft2.wav",
    "sound/physics/body/body_medium_impact_soft3.wav",
    "sound/physics/body/body_medium_impact_soft4.wav",
    "sound/physics/body/body_medium_impact_soft5.wav",
    "sound/physics/body/body_medium_impact_soft6.wav",
    "sound/physics/body/body_medium_impact_soft7.wav"
]

class Ragdoll(PhysRagdoll):

    def __init__(self, characterNp, collInfo):
        PhysRagdoll.__init__(self, characterNp)
        for hard in HardSounds:
            sound = base.audio3ds[0].loadSfx(hard)
            sound.set3dDistanceFactor(0.07)
            self.addHardImpactSound(sound)
        for soft in SoftSounds:
            sound.set3dDistanceFactor(0.07)
            sound = base.audio3ds[0].loadSfx(soft)
            self.addSoftImpactSound(sound)
        #self.setDebug(True, 4.0)
        self.task = None
        self.collInfo = collInfo
        self.characterNp = characterNp
        self.characterNp.node().setFinal(True)

    def getRagdollPosition(self):
        return Point3(self.getJointActor(self.collInfo.root_part).getTransform().getPos())

    def setup(self):
        #collideWith = {}
        for i in range(self.collInfo.getNumParts()):
            part = self.collInfo.getPart(i)
            meshData = PhysConvexMeshData(part.mesh_data)
            mesh = PhysConvexMesh(meshData)
            shape = PhysShape(mesh, PhysMaterial(0.25, 0.5, 0.75))
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

            forceJoint.addForce(forceVector, forceJoint.FTImpulse)
            forcePos = Point3(forceJoint.getTransform().getPos())

            if forcePos != Point3():
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

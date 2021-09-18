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
            self.addHardImpactSound(base.audio3ds[0].loadSfx(hard))
        for soft in SoftSounds:
            self.addSoftImpactSound(base.audio3ds[0].loadSfx(soft))
        #self.setDebug(True, 4.0)
        self.task = None
        self.collInfo = collInfo

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
        return task.cont

    def destroy(self):
        if self.task:
            self.task.remove()
        self.task = None
        PhysRagdoll.destroy(self)

    def setEnabled(self, enable, forceJointName, forceVector, forcePos):
        if enable:
            self.startRagdoll(base.physicsWorld, base.render)
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

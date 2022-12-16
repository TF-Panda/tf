"""WeaponShell module: contains the WeaponShell class."""

from panda3d.pphysics import *
from panda3d.core import *

from direct.directbase import DirectRender

from tf.actor.Model import Model
from tf.tfbase.SurfaceProperties import SurfaceProperties
from tf.tfbase import CollisionGroups

import random

class WeaponShell:
    """
    A small physics object emitted from a weapon -- a shell ejection.

    The shell is thrown in a random direction from a user provided position,
    and plays a single bounce sound on the first bounce.  The shell is
    removed as soon as it goes to sleep, or after a user-configured max
    lifetime if it has not yet gone to sleep.

    There can also only be a maximum number of shells at once, to save on
    physics and rendering resources.  The max number of shells is specified
    in Config.prc.
    """

    AllShells = []
    # The maximum number of shells we can have in the world at once.
    MaxShells = ConfigVariableInt("tf-max-shells", 20)
    # The maximum amount of time the shell is allowed to stay around
    # without going to sleep.  We force remove the shell after this
    # amount of time if it hasn't gone to sleep yet.
    MaxShellLifetime = ConfigVariableDouble("tf-max-shell-lifetime", 2.5)

    def __init__(self, modelFilename, pos, quat, amplitude, inheritVelocity, bounceSound):
        mdl = Model()
        if not mdl.loadModel(modelFilename):
            mdl.cleanup()
            return
        self.mdl = mdl
        self.bounced = False
        self.bounceSound = bounceSound

        # Give it the silent surfaceprop so we can do a manual bounce
        # sound.
        surfaceProp = "default_silent"
        surfaceDef = SurfaceProperties.get(surfaceProp)
        assert surfaceDef

        # TODO: put this in a common place, there is a lot of duplication
        # for creating a physics shape from a model's collision info.
        cinfo = mdl.modelRootNode.getCollisionInfo()
        cpart = cinfo.getPart(0)
        assert not cpart.concave
        cmesh = PhysConvexMesh(PhysConvexMeshData(cpart.mesh_data))
        cshape = PhysShape(cmesh, surfaceDef.getPhysMaterial())
        cnode = PhysRigidDynamicNode("shell")
        cnode.addShape(cshape)
        cnode.computeMassProperties()
        cnode.setMass(cpart.mass)
        cnode.setLinearDamping(cpart.damping)
        cnode.setAngularDamping(cpart.rot_damping)
        cnode.setFromCollideMask(CollisionGroups.Debris)
        cnode.setIntoCollideMask(CollisionGroups.World)
        cnode.setCcdEnabled(True)
        #cnode.setContactCallback(CallbackObject.make(self.__contactCallback))
        #cnode.setSleepCallback(CallbackObject.make(self.__sleepCallback))
        cnode.setSleepThreshold(0.25)
        cnode.addToScene(base.physicsWorld)
        cnp = base.dynRender.attachNewNode(cnode)
        cnp.node().setFinal(True)
        cnp.setPos(pos)
        q = Quat()
        lookAt(q, quat.getUp())
        cnp.setQuat(q)
        cnp.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
        cnp.showThrough(DirectRender.ShadowCameraBitmask)
        cnode.syncTransform()
        mdl.modelNp.reparentTo(cnp)

        # Set up the ejection velocity.
        cnode.addForce(quat.getForward() * amplitude + inheritVelocity, cnode.FTVelocityChange)

        WeaponShell.AllShells.append(self)
        if len(WeaponShell.AllShells) > WeaponShell.MaxShells.value:
            WeaponShell.AllShells[0].cleanup()

        self.mdl = mdl
        self.cnp = cnp
        self.dieTask = base.taskMgr.doMethodLater(WeaponShell.MaxShellLifetime.value, self.__forceDie, 'shellForceDie')

    def __forceDie(self, task):
        self.cleanup()
        return task.done

    def __contactCallback(self, cbdata):
        if self.bounced or not self.bounceSound:
            return

        # Play the one-time bounce sound.
        base.world.emitSoundSpatial(self.bounceSound, cbdata.getContactPair(0).getContactPoint(0).getPosition())
        self.bounced = True

    def __sleepCallback(self, cbdata):
        if cbdata.isAsleep():
            # Remove shell as soon as we go to sleep.
            self.cleanup()

    def cleanup(self):
        self.dieTask.remove()
        self.dieTask = None
        self.mdl.cleanup()
        self.mdl = None
        self.cnp.node().removeFromScene(base.physicsWorld)
        self.cnp.removeNode()
        self.cnp = None
        WeaponShell.AllShells.remove(self)


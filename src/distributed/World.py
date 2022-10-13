from tf.entity.DistributedSolidEntity import DistributedSolidEntity

from panda3d.core import *
from panda3d.pphysics import *

from direct.directbase import DirectRender
from tf.tfbase.TFGlobals import Contents, TakeDamage, SolidShape, SolidFlag, WorldParent

class World(DistributedSolidEntity):

    def __init__(self):
        DistributedSolidEntity.__init__(self)
        self.takeDamageMode = TakeDamage.No

        self.solidShape = SolidShape.Model
        self.solidFlags = SolidFlag.Tangible
        self.physType = self.PTTriangles
        self.parentEntityId = WorldParent.Render

    def generate(self):
        DistributedSolidEntity.generate(self)
        base.world = self

        # Link static prop physics to world entity.
        for np in base.game.propPhysRoot.findAllMatches("**/+PhysRigidActorNode"):
            np.setPythonTag("entity", self)
            np.setPythonTag("object", self)

    def announceGenerate(self):
        DistributedSolidEntity.announceGenerate(self)
        self.initializeCollisions()
        #self.node().setCcdEnabled(True)

        # Enable Z-prepass on the world geometry.
        self.setAttrib(DepthPrepassAttrib.make(DirectRender.MainCameraBitmask|DirectRender.ReflectionCameraBitmask))
        self.flattenLight()

    def delete(self):
        base.world = None
        DistributedSolidEntity.delete(self)

if not IS_CLIENT:
    WorldAI = World
    WorldAI.__name__ = 'WorldAI'

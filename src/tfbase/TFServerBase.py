from direct.showbase.HostBase import HostBase
from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.TFServerRepository import TFServerRepository

from tf.tfbase import Sounds, TFGlobals

from panda3d.core import *
from panda3d.pphysics import *

class TFServerBase(HostBase):
    notify = directNotify.newCategory("TFServerBase")

    def __init__(self):
        HostBase.__init__(self)

        Sounds.loadSounds(True)

        self.render = NodePath("render")
        self.hidden = NodePath("hidden")

        PhysSystem.ptr().initialize()
        self.physicsWorld = PhysScene()
        self.physicsWorld.setGravity((0, 0, -800))
        self.physicsWorld.setFixedTimestep(0.015)

        planeMat = PhysMaterial(0.4, 0.25, 0.2)
        planeShape = PhysShape(PhysPlane(LPlane(0, 0, 1, 0)), planeMat)
        planeActor = PhysRigidStaticNode("plane")
        planeActor.addShape(planeShape)
        planeActor.addToScene(self.physicsWorld)
        planeActor.setIntoCollideMask(BitMask32.allOn())
        planeNp = self.render.attachNewNode(planeActor)
        planeNp.setPos(0, 0, 0)

        self.simTaskMgr.add(self.__physicsUpdate, 'serverPhysicsUpdate', sort = 50)

        self.sv = TFServerRepository(self.config.GetInt("sv_port", 6667))
        self.air = self.sv
        self.sr = self.sv
        self.net = self.sv

    def __physicsUpdate(self, task):
        self.physicsWorld.simulate(globalClock.getDt())
        return task.cont

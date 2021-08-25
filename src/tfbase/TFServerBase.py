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

        if self.config.GetBool('want-server-pstats', False):
            PStatClient.connect()

        self.render = NodePath("render")
        self.hidden = NodePath("hidden")

        if self.config.GetBool("phys-enable-pvd-server", False):
            loadPrcFileData("", "phys-enable-pvd 1")
        else:
            loadPrcFileData("", "phys-enable-pvd 0")

        PhysSystem.ptr().initialize()
        self.physicsWorld = PhysScene()
        self.physicsWorld.setGravity((0, 0, -800)) # 9.81 m/s as inches
        self.physicsWorld.setFixedTimestep(0.015)

        self.physicsWorld.setGroupCollisionFlag(
            TFGlobals.CollisionGroup.PlayerMovement, TFGlobals.CollisionGroup.Debris, False)
        #self.physicsWorld.setGroupCollisionFlag(
        #    TFGlobals.CollisionGroup.PlayerMovement, TFGlobals.CollisionGroup.Rockets, False)
        self.physicsWorld.setGroupCollisionFlag(
            TFGlobals.CollisionGroup.PlayerMovement, TFGlobals.CollisionGroup.Projectile, False)

        self.simTaskMgr.add(self.__physicsUpdate, 'serverPhysicsUpdate', sort = 50)

        self.sv = TFServerRepository(self.config.GetInt("sv_port", 6667))
        self.air = self.sv
        self.sr = self.sv
        self.net = self.sv

        precacheList = [
            "tfmodels/src/buildables/sentry1.pmdl",
            "tfmodels/src/char/engineer/engineer.pmdl",
            "tfmodels/src/char/engineer/engineer_viewmodel/c_engineer_arms.pmdl",
            "tfmodels/src/char/soldier/soldier.pmdl",
            "tfmodels/src/char/soldier/soldier_viewmodel/c_soldier_arms.pmdl",
            "tfmodels/src/weapons/rocketlauncher/c_rocketlauncher.pmdl",
            "tfmodels/src/weapons/shotgun/c_shotgun.pmdl",
            "tfmodels/src/weapons/pistol/c_pistol.pmdl",
            "tfmodels/src/weapons/wrench/c_wrench.pmdl",
            "tfmodels/src/buildables/sentry2_heavy.pmdl",
            "tfmodels/src/buildables/sentry2.pmdl",
            "tfmodels/src/buildables/sentry1_gib1.pmdl",
            "tfmodels/src/buildables/sentry1_gib2.pmdl",
            "tfmodels/src/buildables/sentry1_gib3.pmdl",
            "tfmodels/src/buildables/sentry1_gib4.pmdl",
            "tfmodels/src/weapons/rocketlauncher/w_rocket.pmdl",
            "tfmodels/src/char/demo/demo.pmdl",
            "tfmodels/src/char/demo/demo_viewmodel/c_demo_arms.pmdl",
            "tfmodels/src/weapons/bottle/c_bottle.pmdl",
            "tfmodels/src/weapons/shovel/c_shovel.pmdl"
        ]
        self.precache = []
        for pc in precacheList:
            self.precache.append(loader.loadModel(pc))

    def restart(self):
        ShowBase.restart(self)
        # This task is added by ShowBase automatically for the built-in
        # collision system, which we do not use.  Remove it.
        self.taskMgr.remove('resetPrevTransform')

    def preRunFrame(self):
        PStatClient.mainTick()
        HostBase.preRunFrame(self)

    def postRunFrame(self):
        HostBase.postRunFrame(self)
        elapsed = self.globalClock.getRealTime() - self.frameTime
        # Sleep for a fraction of the simulation tick interval.  The server
        # only does stuff on simulation ticks.
        minDt = self.intervalPerTick * 0.1
        if elapsed < minDt:
            Thread.sleep(minDt - elapsed)

    def __physicsUpdate(self, task):
        self.physicsWorld.simulate(globalClock.getDt())
        return task.cont

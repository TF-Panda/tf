from direct.showbase.HostBase import HostBase
from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.TFServerRepository import TFServerRepository

from tf.tfbase import Sounds, TFGlobals

from panda3d.core import *
from panda3d.pphysics import *

# Note: The server needs to maintain a minimum of 66 "frames" or simulation
# ticks per second.  There's a lot more leeway since the server isn't
# rendering anything like the client, but the server does a lot more
# simulation work.

class TFServerBase(HostBase):
    notify = directNotify.newCategory("TFServerBase")

    def __init__(self):
        HostBase.__init__(self)

        Sounds.loadSounds(True)

        self.showingBounds = False

        if self.config.GetBool('want-server-pstats', False):
            PStatClient.connect()

        self.render = NodePath("render")
        self.dynRender = NodePath("dynamic")
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
        self.sv.game.changeLevel("test_steam_audio")

        precacheList = [
            "models/buildables/sentry1",
            "models/char/engineer",
            "models/char/c_engineer_arms",
            "models/char/soldier",
            "models/char/c_soldier_arms",
            "models/weapons/c_rocketlauncher",
            "models/weapons/c_shotgun",
            "models/weapons/c_pistol",
            "models/weapons/c_wrench",
            "models/buildables/sentry2_heavy",
            "models/buildables/sentry2",
            "models/buildables/sentry1_gib1",
            "models/buildables/sentry1_gib2",
            "models/buildables/sentry1_gib3",
            "models/buildables/sentry1_gib4",
            "models/weapons/w_rocket",
            "models/char/demo",
            "models/char/c_demo_arms",
            "models/weapons/c_bottle",
            "models/weapons/c_shovel",
            "models/char/heavy"
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
        #elapsed = self.globalClock.getRealTime() - self.frameTime
        # Sleep for a fraction of the simulation tick interval.  The server
        # only does stuff on simulation ticks.
        #minDt = self.intervalPerTick * 0.1
        #if elapsed < minDt:
        #    Thread.sleep(minDt - elapsed)

    def __physicsUpdate(self, task):
        self.physicsWorld.simulate(globalClock.getDt())
        return task.cont

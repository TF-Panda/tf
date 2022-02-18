from direct.showbase.HostBase import HostBase
from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.TFServerRepository import TFServerRepository

from tf.tfbase import Sounds, TFGlobals, SurfaceProperties

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
        SurfaceProperties.loadSurfaceProperties()

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
        self.sv.game.changeLevel("tr_target")

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
        dt = globalClock.getDt()

        self.physicsWorld.simulate(dt)

        # Process global contact events, play sounds.
        while self.physicsWorld.hasContactEvent():
            data = self.physicsWorld.popContactEvent()

            if data.getNumContactPairs() == 0:
                continue

            pair = data.getContactPair(0)
            if not pair.isContactType(PhysEnums.CTFound):
                continue

            if pair.getNumContactPoints() == 0:
                continue

            point = pair.getContactPoint(0)

            speed = point.getImpulse().length()
            if speed < 70.0:
                continue

            #a = data.getActorA()
            #b = data.getActorB()

            position = point.getPosition()

            volume = speed * speed * (1.0 / (320.0 * 320.0))
            volume = min(1.0, volume)

            matA = point.getMaterialA(pair.getShapeA())
            matB = point.getMaterialB(pair.getShapeB())

            #force = speed / dt

            # Play sounds from materials of both surfaces.
            # This is more realistic, Source only played from one material.
            if matA:
                surfDefA = SurfaceProperties.SurfacePropertiesByPhysMaterial.get(matA)
                if surfDefA:
                    if speed >= 500:
                        base.world.emitSoundSpatial(surfDefA.impactHard, position, volume)
                    elif speed >= 100:
                        base.world.emitSoundSpatial(surfDefA.impactSoft, position, volume)
            if matB:
                surfDefB = SurfaceProperties.SurfacePropertiesByPhysMaterial.get(matB)
                if surfDefB:
                    if speed >= 500:
                        base.world.emitSoundSpatial(surfDefB.impactHard, position, volume)
                    elif speed >= 100:
                        base.world.emitSoundSpatial(surfDefB.impactSoft, position, volume)


        return task.cont

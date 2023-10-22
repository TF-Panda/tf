from panda3d.core import *
loadPrcFileData("", "job-system-num-worker-threads 0")
from panda3d.pphysics import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.HostBase import HostBase
from tf.distributed.TFServerRepository import TFServerRepository
from tf.entity.EntityConnectionManager import EntityConnectionManager
from tf.entity.EntityManager import EntityManager
from tf.tfbase import Sounds, SurfaceProperties, TFGlobals

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
        self.sky3DRoot = NodePath("sky3DRoot")
        self.hidden = NodePath("hidden")

        if self.config.GetBool("phys-enable-pvd-server", False):
            loadPrcFileData("server-init", "phys-enable-pvd 1")
        else:
            loadPrcFileData("server-init", "phys-enable-pvd 0")

        # Don't read fat texture data on the server.  Saves memory.
        loadPrcFileData("server-init", "textures-header-only 1")
        loadPrcFileData("server-init", "is-server 1")
        loadPrcFileData("server-init", "interpolate-frames 0")

        PhysSystem.ptr().initialize()
        self.physicsWorld = PhysScene()
        self.physicsWorld.setGravity((0, 0, -800)) # 9.81 m/s as inches
        self.physicsWorld.setFixedTimestep(0.015)

        if ConfigVariableBool('garbage-collect-states').value:
            self.simTaskMgr.add(self.__garbageCollectStates, 'serverGarbageCollect', sort = -100)
        self.simTaskMgr.add(self.__physicsUpdate, 'serverPhysicsUpdate', sort = 50)

        self.entMgr = EntityManager()

        self.simTaskMgr.add(EntityConnectionManager.processIOQueue, 'processEntityIOQueue', sort=0)

        self.sv = TFServerRepository(self.config.GetInt("sv_port", 6667))
        self.air = self.sv
        self.sr = self.sv
        self.net = self.sv
        self.sv.game.changeLevel(ConfigVariableString('tf-map', 'ctf_2fort').value)

        self.precache = []
        for pc in TFGlobals.ModelPrecacheList:
            self.precache.append(loader.loadModel(pc))

    def __garbageCollectStates(self, task):
        TransformState.garbageCollect()
        RenderState.garbageCollect()
        return task.cont

    def preRunFrame(self):
        PStatClient.mainTick()
        HostBase.preRunFrame(self)

    def postRunFrame(self):
        HostBase.postRunFrame(self)
        self.globalClock.tick()
        elapsed = self.clockMgr.getDeltaTime()
        # Sleep for a fraction of the simulation tick interval.  The server
        # only does stuff on simulation ticks.
        minDt = self.intervalPerTick * 0.08
        if elapsed < minDt:
            Thread.sleep(minDt - elapsed)

    def __physicsUpdate(self, task):
        self.physicsWorld.simulate(self.clock.getFrameTime())

        chan = Sounds.Channel.CHAN_STATIC

        # Process global contact events, play sounds.
        while self.physicsWorld.hasContactEvent():
            data = self.physicsWorld.popContactEvent()
            if not data.isValid():
                continue

            if data.getNumContactPairs() == 0:
                continue

            pair = data.getContactPair(0)
            if not pair.isContactType(PhysEnums.CTFound):
                continue

            if pair.getNumContactPoints() == 0:
                continue

            point = pair.getContactPoint(0)

            speed = point.getImpulse().length()
            a = data.getActorA()
            if not a:
                continue
            speed /= a.getMass()
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
            else:
                surfDefA = None
            if matB:
                surfDefB = SurfaceProperties.SurfacePropertiesByPhysMaterial.get(matB)
            else:
                surfDefB = None

            if surfDefA and surfDefB:
                # If we have an impact sound for both surfaces, divide up the
                # volume between both sounds, so impact sounds are roughly the
                # same volume as Source.
                volume *= 0.5

            if speed >= 500:
                if surfDefA:
                    base.world.emitSoundSpatial(surfDefA.impactHard, position, volume, chan=chan)
                if surfDefB:
                    base.world.emitSoundSpatial(surfDefB.impactHard, position, volume, chan=chan)
            elif speed >= 70:
                if surfDefA:
                    base.world.emitSoundSpatial(surfDefA.impactSoft, position, volume, chan=chan)
                if surfDefB:
                    base.world.emitSoundSpatial(surfDefB.impactSoft, position, volume, chan=chan)

        return task.cont

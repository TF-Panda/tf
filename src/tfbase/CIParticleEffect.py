"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.
@file CIParticleEffect.py
@author Brian Lach
@date June 20, 2018
"""

from direct.particles.ParticleEffect import ParticleEffect

class CIParticleEffect(ParticleEffect):
    """Allows particles to softStop and then be automatically cleaned up once the remaining particles die away."""

    def __init__(self, *args, **kwargs):
        ParticleEffect.__init__(self, *args, **kwargs)
        self.cleanupTask = None

    def __startCleanupTask(self):
        self.__stopCleanupTask()

        # Allow the existing particles to die off completely before cleaning up the particle system.
        # Figure out the max lifespan.
        maxLifespan = 0.0
        for particles in self.getParticlesList():
            lifespan = particles.factory.getLifespanBase()
            if lifespan > maxLifespan:
                maxLifespan = lifespan

        self.cleanupTask = taskMgr.doMethodLater(maxLifespan, self.__cleanupTask, "CIParticleEffect.cleanupTask")

    def __cleanupTask(self, task):
        # All of the remaining particles should have died off by now.
        # We're safe to cleanup the particle effect.
        self.cleanup()
        return task.done

    def __stopCleanupTask(self):
        if self.cleanupTask:
            self.cleanupTask.remove()
        self.cleanupTask = None

    def softStop(self):
        try:
            ParticleEffect.softStop(self)
        except:
            return

        self.__startCleanupTask()

    def cleanup(self):
        self.__stopCleanupTask()
        try:
            ParticleEffect.cleanup(self)
        except:
            pass

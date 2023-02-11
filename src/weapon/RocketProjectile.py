from .BaseRocket import BaseRocket

from panda3d.core import *

class RocketProjectile(BaseRocket):

    def __init__(self):
        BaseRocket.__init__(self)

        if IS_CLIENT:
            self.trailsEffect = None

    if not IS_CLIENT:
        def generate(self):
            self.setModel("models/weapons/w_rocket")
            BaseRocket.generate(self)
    else:
        def announceGenerate(self):
            BaseRocket.announceGenerate(self)
            self.trailsEffect = self.makeTrailsEffect(self)
            self.trailsEffect.start(base.dynRender)

        #def onUnhideRocket(self):
        #    if self.trailsEffect:
        #        self.trailsEffect.start(base.dynRender)

        def disable(self):
            if self.trailsEffect:
                self.trailsEffect.softStop()
                self.trailsEffect = None
            BaseRocket.disable(self)


if not IS_CLIENT:
    RocketProjectileAI = RocketProjectile
    RocketProjectileAI.__name__ = 'RocketProjectileAI'

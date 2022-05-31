from .BaseRocket import BaseRocket

from tf.tfbase.CIParticleEffect import CIParticleEffect

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
            self.setModel("models/weapons/w_rocket")
            self.trailsEffect = CIParticleEffect()
            self.trailsEffect.loadConfig('rockettrail.ptf')
            self.trailsEffect.start(self, base.dynRender)
            for p in self.trailsEffect.particlesDict.values():
                p.getRenderer().getRenderNodePath().setDepthWrite(False, 10)

        def disable(self):
            if self.trailsEffect:
                self.trailsEffect.softStop()
                self.trailsEffect = None
            BaseRocket.disable(self)


if not IS_CLIENT:
    RocketProjectileAI = RocketProjectile
    RocketProjectileAI.__name__ = 'RocketProjectileAI'

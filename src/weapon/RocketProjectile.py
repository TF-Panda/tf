from .BaseRocket import BaseRocket

class RocketProjectile(BaseRocket):

    def __init__(self):
        BaseRocket.__init__(self)

    if not IS_CLIENT:
        def generate(self):
            self.setModel("tfmodels/src/weapons/rocketlauncher/w_rocket.pmdl")
            BaseRocket.generate(self)

if not IS_CLIENT:
    RocketProjectileAI = RocketProjectile
    RocketProjectileAI.__name__ = 'RocketProjectileAI'

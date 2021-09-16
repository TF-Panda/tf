from .BaseRocket import BaseRocket

class RocketProjectile(BaseRocket):

    def __init__(self):
        BaseRocket.__init__(self)

    if not IS_CLIENT:
        def generate(self):
            self.setModel("models/weapons/w_rocket")
            BaseRocket.generate(self)

if not IS_CLIENT:
    RocketProjectileAI = RocketProjectile
    RocketProjectileAI.__name__ = 'RocketProjectileAI'

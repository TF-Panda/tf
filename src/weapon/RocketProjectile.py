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
        def makeTrailsEffect(self):
            system = ParticleSystem2()
            system.setPoolSize(190)

            system.setInput(0, self, False)

            emitter = ContinuousParticleEmitter()
            emitter.setEmissionRate(125)
            system.addEmitter(emitter)

            ################
            # Initializers #
            ################
            system.addInitializer(P2_INIT_PositionSphereVolume((0, 0, 0), 1, 1))
            system.addInitializer(P2_INIT_LifespanRandomRange(1, 1.5))
            system.addInitializer(P2_INIT_ScaleRandomRange(Vec3(4), Vec3(5)))
            system.addInitializer(P2_INIT_ColorRandomRange(Vec3(0.6, 0.6, 0.65), Vec3(0.6, 0.6, 0.65)))
            system.addInitializer(P2_INIT_RotationRandomRange(0, 25, 85))
            system.addInitializer(P2_INIT_RotationVelocityRandomRange(20, 30, 1.0, True))

            #############
            # Functions #
            #############

            scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
            l0 = ParticleLerpSegment()
            l0.type = l0.LTLinear
            l0.start = 0.0
            l0.end = 1.0
            l0.start_is_initial = True
            l0.end_value = Vec3(13.0)
            scaleLerp.addSegment(l0)
            system.addFunction(scaleLerp)

            alphaLerp = LerpParticleFunction(LerpParticleFunction.CAlpha)
            l0 = ParticleLerpSegment()
            l0.type = l0.LTLinear
            l0.start = 0.5
            l0.end = 1.0
            l0.start_value = Vec3(1.0)
            l0.end_value = Vec3(0.0)
            alphaLerp.addSegment(l0)
            system.addFunction(alphaLerp)

            system.addFunction(LinearMotionParticleFunction())
            system.addFunction(LifespanKillerParticleFunction())
            system.addFunction(AngularMotionParticleFunction())

            system.addForce(VectorParticleForce(Vec3.up() * 8))

            # Render particles as sprites with a smoke texture.
            renderer = SpriteParticleRenderer2()
            state = RenderState.make(MaterialAttrib.make(loader.loadMaterial("tfmodels/src/materials/particle_rockettrail1.pmat")),
                                    ColorAttrib.makeVertex())
            renderer.setRenderState(state)
            system.addRenderer(renderer)

            return system

        def announceGenerate(self):
            BaseRocket.announceGenerate(self)
            self.trailsEffect = self.makeTrailsEffect()
            self.trailsEffect.start(base.dynRender)

        def disable(self):
            if self.trailsEffect:
                self.trailsEffect.softStop()
                self.trailsEffect = None
            BaseRocket.disable(self)


if not IS_CLIENT:
    RocketProjectileAI = RocketProjectile
    RocketProjectileAI.__name__ = 'RocketProjectileAI'

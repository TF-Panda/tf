from panda3d.core import *

BloodGoopEffect = None
def getBloodGoopEffect():
    global BloodGoopEffect
    if not BloodGoopEffect:
        system = ParticleSystem2()
        system.setPoolSize(1)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(0.5)
        system.addEmitter(emitter)

        system.addInitializer(P2_INIT_PositionSphereVolume((0, 0, 0), 1, 1, (1, 1, 1)))
        system.addInitializer(P2_INIT_LifespanRandomRange(0.25, 0.25))
        system.addInitializer(P2_INIT_ColorRandomRange(Vec3(1, 0, 0), Vec3(1.0, 0.2, 0.2)))
        system.addInitializer(P2_INIT_ScaleRandomRange(Vec3(13), Vec3(16), False))
        system.addInitializer(P2_INIT_AnimationIndexRandom(0, 3))
        system.addInitializer(P2_INIT_AnimationFPSRandom(56, 56))
        system.addInitializer(P2_INIT_RotationRandomRange(0.0, 0.0, 360.0))

        slerp = ParticleLerpSegment()
        slerp.type = slerp.LTLinear
        slerp.start = 0.7
        slerp.end = 1.0
        slerp.start_value = Vec3(1.0)
        slerp.end_value = Vec3(0.0)
        slerpFunc = LerpParticleFunction(LerpParticleFunction.CAlpha)
        slerpFunc.addSegment(slerp)
        system.addFunction(slerpFunc)

        system.addFunction(LifespanKillerParticleFunction())

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(RenderState.make(MaterialAttrib.make(loader.loadMaterial("tfmodels/blood_goop3.pmat")),
                                                ColorAttrib.makeVertex()))
        system.addRenderer(renderer)

        BloodGoopEffect = system

    return BloodGoopEffect.makeCopy()

from panda3d.core import *

PlayerFire = None
def getPlayerFireEffect():
    global PlayerFire
    if not PlayerFire:

        system = ParticleSystem2()
        system.setPoolSize(255)
        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(255)
        system.addEmitter(emitter)

        system.addInitializer(P2_INIT_LifespanRandomRange(0.8, 1.0))
        system.addInitializer(P2_INIT_PositionModelHitBoxes(0))
        system.addInitializer(P2_INIT_ScaleRandomRange(5, 7, False))
        system.addInitializer(P2_INIT_AnimationIndexRandom(0, 4))
        #system.addInitializer(P2_INIT_ColorRandomRange((0.2, 0.3, 0.8), (0.3, 0.5, 1.0)))

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 0.7
        seg.start_value = Vec3(1.0)
        seg.end_value = Vec3(1.0, 0.5, 0.0)
        colorLerp.addSegment(seg)
        system.addFunction(colorLerp)

        alphaLerp = LerpParticleFunction(LerpParticleFunction.CAlpha)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 0.1
        seg.start_value = 0.0
        seg.end_value = 1.0
        alphaLerp.addSegment(seg)
        seg.start = 0.5
        seg.end = 1.0
        seg.start_value = 1.0
        seg.end_value = 0.0
        alphaLerp.addSegment(seg)
        system.addFunction(alphaLerp)

        system.addFunction(LinearMotionParticleFunction(0))
        system.addFunction(LifespanKillerParticleFunction())

        system.addForce(VectorParticleForce((0, 0, 64)))

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(
            RenderState.make(MaterialAttrib.make(loader.loadMaterial("tfmodels/flamethrowerfire102.pmat")),
                             ColorAttrib.makeVertex())
        )
        renderer.setFitAnimationsToParticleLifespan(True)
        system.addRenderer(renderer)

        PlayerFire = system
    return PlayerFire.makeCopy()

RocketBackBlast = None
def getRocketBackBlastEffect():
    global RocketBackBlast
    if not RocketBackBlast:
        system = ParticleSystem2()
        system.setPoolSize(12)
        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(64)
        emitter.setDuration(0.1)
        system.addEmitter(emitter)
        system.addInitializer(P2_INIT_LifespanRandomRange(1.5, 2))
        system.addInitializer(P2_INIT_PositionSphereVolume((0, 0, 0), 1, 2))
        system.addInitializer(P2_INIT_VelocityRadiate((0, -4, 0), 80, 100))
        system.addInitializer(P2_INIT_RotationRandomRange(0, 0, 360))
        system.addInitializer(P2_INIT_ColorRandomRange((255/255, 236/255, 77/255), (255/255, 136/255, 18/255)))
        system.addInitializer(P2_INIT_AlphaRandomRange(128/255, 200/255))
        system.addInitializer(P2_INIT_RotationVelocityRandomRange(10, 20, True))
        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 0.05
        seg.start_is_initial = True
        seg.end_value = Vec3(117/255, 108/255, 108/255)
        colorLerp.addSegment(seg)
        system.addFunction(colorLerp)
        alphaLerp = LerpParticleFunction(LerpParticleFunction.CAlpha)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 1.0
        seg.start_is_initial = True
        seg.end_value = 0.0
        alphaLerp.addSegment(seg)
        system.addFunction(alphaLerp)
        scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
        seg = ParticleLerpSegment()
        seg.type = seg.LTExponential
        seg.exponent = 0.3
        seg.start = 0.0
        seg.end = 1.0
        seg.start_value = 4
        seg.end_value = 7
        scaleLerp.addSegment(seg)
        system.addFunction(scaleLerp)
        #rotLerp = LerpParticleFunction(LerpParticleFunction.CRotation)
        #seg = ParticleLerpSegment()
        #seg.type = seg.LTSinusoid
        #seg.start = 0
        #seg.end = 1.0

        system.addFunction(LinearMotionParticleFunction(5))
        system.addFunction(AngularMotionParticleFunction())
        system.addFunction(LifespanKillerParticleFunction())
        system.addForce(VectorParticleForce((0, 0, 80)))

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(
            RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/smoke2lit.mto")),
                             ColorAttrib.makeVertex())
        )
        renderer.setFitAnimationsToParticleLifespan(True)
        system.addRenderer(renderer)

        RocketBackBlast = system

    return RocketBackBlast.makeCopy()

StickybombPulse = [None, None]
def getStickybombPulseEffect(team):
    if not StickybombPulse[team]:
        from tf.tfbase import TFGlobals
        system = ParticleSystem2()
        system.setPoolSize(3)
        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(10)
        emitter.setDuration(0.6)
        system.addEmitter(emitter)
        system.addInitializer(P2_INIT_PositionExplicit((0, 0, 0)))
        system.addInitializer(P2_INIT_LifespanRandomRange(0.1, 0.1))
        if team == TFGlobals.TFTeam.Red:
            color = Vec3(255/255, 191/255, 116/255)
        else:
            color = Vec3(0, 96/255, 255/255)
        system.addInitializer(P2_INIT_ColorRandomRange(color, color))

        alphaLerp = LerpParticleFunction(LerpParticleFunction.CAlpha)
        seg = ParticleLerpSegment()
        # Fade in
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 0.2
        seg.start_value = 0.0
        seg.end_value = 1.0
        alphaLerp.addSegment(seg)
        # Fade out
        seg.start = 0.2
        seg.end = 1.0
        seg.start_value = 1.0
        seg.end_value = 0.0
        alphaLerp.addSegment(seg)
        system.addFunction(alphaLerp)

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        seg = ParticleLerpSegment()
        seg.type = seg.LTExponential
        seg.exponent = 2
        seg.start = 0.0
        seg.end = 1.0
        seg.start_is_initial = True
        if team == TFGlobals.TFTeam.Red:
            seg.end_value = Vec3(255/255, 62/255, 62/255)
        else:
            seg.end_value = Vec3(62/255, 171/255, 255/255)
        colorLerp.addSegment(seg)
        system.addFunction(colorLerp)

        scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 1.0
        seg.scale_on_initial = True
        seg.start_value = 0.0001
        seg.end_value = 20.0
        scaleLerp.addSegment(seg)
        system.addFunction(scaleLerp)

        system.addFunction(FollowInputParticleFunction(0))
        system.addFunction(LifespanKillerParticleFunction())

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(
            RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/circle1.mto")),
                             ColorAttrib.makeVertex())
        )
        system.addRenderer(renderer)

        StickybombPulse[team] = system

    return StickybombPulse[team].makeCopy()

PipebombTimer = [None, None]
def getPipebombTimerEffect(team):
    if not PipebombTimer[team]:
        from tf.tfbase import TFGlobals

        # Timer child
        system2 = ParticleSystem2()
        system2.setPoolSize(51)
        emitter2 = ContinuousParticleEmitter()
        emitter2.setEmissionRate(16)
        emitter2.setDuration(2.0)
        system2.addEmitter(emitter2)
        system2.addInitializer(P2_INIT_LifespanRandomRange(0.4, 0.4))
        system2.addInitializer(P2_INIT_PositionExplicit((0, 0, 0)))
        system2.addInitializer(P2_INIT_ScaleRandomRange(20, 20, False))
        system2.addInitializer(P2_INIT_AlphaRandomRange(200/255, 200/255))
        if team == TFGlobals.TFTeam.Red:
            color = Vec3(255/255, 180/255, 0)
        else:
            color = Vec3(0, 96/255, 255/255)
        system2.addInitializer(P2_INIT_ColorRandomRange(color, color, False))

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        seg = ParticleLerpSegment()
        seg.type = seg.LTExponential
        seg.exponent = 2
        seg.start_is_initial = True
        seg.start = 0.0
        seg.end = 1.0
        if team == TFGlobals.TFTeam.Red:
            seg.end_value = Vec3(255/255, 24/255, 0)
        else:
            seg.end_value = Vec3(62/255, 171/255, 255/255)
        colorLerp.addSegment(seg)
        alphaLerp = LerpParticleFunction(LerpParticleFunction.CAlpha)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 0.2
        seg.scale_on_initial = True
        seg.start_value = 0.0
        seg.end_value = 1.0
        alphaLerp.addSegment(seg)
        seg.start = 0.2
        seg.end = 1.0
        seg.start_value = 1.0
        seg.end_value = 0.0
        alphaLerp.addSegment(seg)
        scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
        seg = ParticleLerpSegment()
        seg.type = seg.LTExponential
        seg.exponent = 2
        seg.scale_on_initial = True
        seg.start = 0.0
        seg.end = 1.0
        seg.start_value = 0.0001
        seg.end_value = 1.0
        scaleLerp.addSegment(seg)
        system2.addFunction(alphaLerp)
        system2.addFunction(colorLerp)
        system2.addFunction(scaleLerp)
        system2.addFunction(FollowInputParticleFunction(0))
        system2.addFunction(LifespanKillerParticleFunction())

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(
            RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/circle1.mto")),
                             ColorAttrib.makeVertex())
        )
        system2.addRenderer(renderer)

        PipebombTimer[team] = system2
    return PipebombTimer[team].makeCopy()

PipebombTrail = [None, None]
def getPipebombTrailEffect(team):
    if not PipebombTrail[team]:

        from tf.tfbase import TFGlobals

        system = ParticleSystem2()
        system.setPoolSize(124)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(255)
        emitter.setStartTime(0.2)
        emitter.setDuration(2.0)
        system.addEmitter(emitter)

        system.addInitializer(P2_INIT_LifespanRandomRange(0.4, 0.4))
        system.addInitializer(P2_INIT_PositionExplicit((0, 0, 0)))
        system.addInitializer(P2_INIT_AlphaRandomRange(60/255, 60/255))
        system.addInitializer(P2_INIT_ScaleRandomRange(10, 10, False))
        if team == TFGlobals.TFTeam.Red:
            color1 = Vec3(85/255, 0, 0)
            color2 = Vec3(255/255, 0, 0)
        else:
            color1 = Vec3(18/255, 0, 255/255)
            color2 = Vec3(0, 96/255, 255/255)
        system.addInitializer(P2_INIT_ColorRandomRange(color1, color2))

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 1.0
        seg.start_is_initial = True
        seg.end_value = Vec3(205/255, 87/255, 0)
        colorLerp.addSegment(seg)
        system.addFunction(colorLerp)

        alphaLerp = LerpParticleFunction(LerpParticleFunction.CAlpha)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.1
        seg.end = 1.0
        seg.scale_on_initial = True
        seg.start_value = 1.0
        seg.end_value = 0.0
        alphaLerp.addSegment(seg)
        system.addFunction(alphaLerp)

        scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 1.0
        seg.scale_on_initial = True
        seg.start_value = 1.0
        seg.end_value = 0.1
        scaleLerp.addSegment(seg)
        system.addFunction(scaleLerp)

        system.addFunction(LifespanKillerParticleFunction())

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(
            RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/sc_softglow.mto")),
                             ColorAttrib.makeVertex())
        )
        system.addRenderer(renderer)

        PipebombTrail[team] = system

    return PipebombTrail[team].makeCopy()

MuzzleFlashEffect = [None, None]
def getMuzzleFlashEffect(isViewModel):
    if not MuzzleFlashEffect[isViewModel]:
        system = ParticleSystem2()
        system.setPoolSize(20)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(10000)
        system.addEmitter(emitter)

        system.addInitializer(P2_INIT_PositionLineSegment((0, 2, 0), (0, 16, 0)))
        system.addInitializer(P2_INIT_LifespanRandomRange(0.2, 0.2))
        #system.addInitializer(P2_INIT_ScaleRandomRange(10, 10))
        if not isViewModel:
            system.addInitializer(P2_INIT_RemapAttribute(P2_INIT_RemapAttribute.APos, 1, 2, 16,
                                                        P2_INIT_RemapAttribute.AScale, 0, 4, 1))
            system.addInitializer(P2_INIT_RemapAttribute(P2_INIT_RemapAttribute.APos, 1, 2, 16,
                                                        P2_INIT_RemapAttribute.AScale, 1, 4, 1))
        else:
            system.addInitializer(P2_INIT_RemapAttribute(P2_INIT_RemapAttribute.APos, 1, 2, 16,
                                                        P2_INIT_RemapAttribute.AScale, 0, 2.5, 1))
            system.addInitializer(P2_INIT_RemapAttribute(P2_INIT_RemapAttribute.APos, 1, 2, 16,
                                                        P2_INIT_RemapAttribute.AScale, 1, 2.5, 1))
        system.addInitializer(P2_INIT_RotationRandomRange(0, 0, 360))
        system.addInitializer(P2_INIT_ColorRandomRange((1, 0.7, 0), (1, 0.7, 0)))
        #system.addInitializer(P2_INIT_RotationRandomRange(0, 0, 360))
        #system.addInitializer(P2_INIT_RotationVelocityRandomRange())

        scaleLerpFunc = LerpParticleFunction(LerpParticleFunction.CScale)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.start = 0.0
        seg.end = 0.25
        seg.scale_on_initial = True
        seg.start_value = 0.5
        seg.end_value = 1.5
        scaleLerpFunc.addSegment(seg)
        seg.start = 0.25
        seg.end = 1.0
        seg.start_value = 1.5
        seg.end_value = 0.5
        scaleLerpFunc.addSegment(seg)
        system.addFunction(scaleLerpFunc)

        colorLerpFunc = LerpParticleFunction(LerpParticleFunction.CRgb)
        seg = ParticleLerpSegment()
        seg.type = seg.LTLinear
        seg.scale_on_initial = True
        seg.start = 0.0
        seg.end = 0.25
        seg.start_value = 0.0
        seg.end_value = 1.0
        colorLerpFunc.addSegment(seg)
        seg.start = 0.25
        seg.end = 1.0
        seg.start_value = 1.0
        seg.end_value = 0.0
        colorLerpFunc.addSegment(seg)
        system.addFunction(colorLerpFunc)

        system.addFunction(AngularMotionParticleFunction())
        system.addFunction(LifespanKillerParticleFunction())

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/starflash01.mto")), ColorAttrib.makeVertex()))
        system.addRenderer(renderer)

        MuzzleFlashEffect[isViewModel] = system
    return MuzzleFlashEffect[isViewModel].makeCopy()

BloodTrailEffect = None
def getBloodTrailEffect():
    global BloodTrailEffect
    if not BloodTrailEffect:
        system = ParticleSystem2()
        system.setPoolSize(25)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(16)
        system.addEmitter(emitter)

        system.addInitializer(P2_INIT_PositionSphereVolume((0, 0, 0), 0, 2, (1, 1, 1)))
        system.addInitializer(P2_INIT_LifespanRandomRange(0.34, 0.6))
        system.addInitializer(P2_INIT_ColorRandomRange(Vec3(255/255, 31/255, 0), Vec3(192/255, 8/255, 5/255)))
        system.addInitializer(P2_INIT_ScaleRandomRange(Vec3(12), Vec3(21), False))
        system.addInitializer(P2_INIT_AlphaRandomRange(160/255, 240/255))
        system.addInitializer(P2_INIT_AnimationIndexRandom(0, 3))
        system.addInitializer(P2_INIT_RotationRandomRange(0.0, 0.0, 360.0))
        system.addInitializer(P2_INIT_RotationVelocityRandomRange(0, 4, 1, True))
        system.addInitializer(P2_INIT_VelocityRadiate((0, 0, 0), 0, 32))

        slerpFunc = LerpParticleFunction(LerpParticleFunction.CAlpha)
        slerp = ParticleLerpSegment()
        slerp.type = slerp.LTLinear
        # Fade in
        slerp.start = 0.0
        slerp.end = 0.1
        slerp.start_value = 0.0
        slerp.end_is_initial = True
        #slerp.end_value = 1.0
        slerpFunc.addSegment(slerp)
        # Fade out
        slerp.start = 0.5
        slerp.end = 1
        #slerp.start_value = 1.0
        slerp.start_is_initial = True
        slerp.end_is_initial = False
        slerp.end_value = 0.0
        slerpFunc.addSegment(slerp)
        system.addFunction(slerpFunc)

        system.addFunction(LinearMotionParticleFunction(0.025))
        system.addFunction(AngularMotionParticleFunction())
        system.addFunction(LifespanKillerParticleFunction())

        system.addForce(VectorParticleForce((0, 0, -100)))

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/blood_goop3.mto")),
                                                ColorAttrib.makeVertex()))
        renderer.setFitAnimationsToParticleLifespan(True)
        system.addRenderer(renderer)
        BloodTrailEffect = system
    return BloodTrailEffect.makeCopy()

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
        system.addInitializer(P2_INIT_LifespanRandomRange(0.2, 0.3))
        system.addInitializer(P2_INIT_ColorRandomRange(Vec3(1, 0, 0), Vec3(1.0, 0.2, 0.2)))
        system.addInitializer(P2_INIT_ScaleRandomRange(Vec3(13), Vec3(16), False))
        system.addInitializer(P2_INIT_AnimationIndexRandom(0, 3))
        system.addInitializer(P2_INIT_RotationRandomRange(0.0, 0.0, 360.0))

        slerpFunc = LerpParticleFunction(LerpParticleFunction.CAlpha)
        slerp = ParticleLerpSegment()
        slerp.type = slerp.LTLinear
        slerp.start = 0.0
        slerp.end = 0.1
        slerp.start_value = 0.0
        slerp.end_value = 1.0
        slerpFunc.addSegment(slerp)
        slerp.start = 0.5
        slerp.end = 1.0
        slerp.start_value = 1.0
        slerp.end_value = 0.0
        slerpFunc.addSegment(slerp)
        system.addFunction(slerpFunc)

        system.addFunction(LifespanKillerParticleFunction())

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/blood_goop3.mto")),
                                                ColorAttrib.makeVertex()))
        renderer.setFitAnimationsToParticleLifespan(True)
        system.addRenderer(renderer)

        BloodGoopEffect = system

    return BloodGoopEffect.makeCopy()

RocketTrailEffect = None
def getRocketTrailEffect():
    global RocketTrailEffect
    if not RocketTrailEffect:
        system = ParticleSystem2()
        system.setPoolSize(190)

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

        system.addFunction(LinearMotionParticleFunction(0.5))
        system.addFunction(LifespanKillerParticleFunction())
        system.addFunction(AngularMotionParticleFunction())

        system.addForce(VectorParticleForce(Vec3.up() * 8))

        # Render particles as sprites with a smoke texture.
        renderer = SpriteParticleRenderer2()
        state = RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/particle_rockettrail1.mto")),
                                ColorAttrib.makeVertex())
        renderer.setRenderState(state)
        system.addRenderer(renderer)

        RocketTrailEffect = system

    return RocketTrailEffect.makeCopy()

OverhealedEffect = [None, None]
def getOverhealedEffect(team):
    global OverhealedEffect
    if not OverhealedEffect[team]:
        from tf.tfbase import TFGlobals

        system = ParticleSystem2()
        system.setPoolSize(30)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(15)
        system.addEmitter(emitter)

        system.addInitializer(P2_INIT_PositionModelHitBoxes(0))
        system.addInitializer(P2_INIT_LifespanRandomRange(2, 2))
        system.addInitializer(P2_INIT_VelocityExplicit(Vec3.up(), 13, 13))
        if team == TFGlobals.TFTeam.Red:
            system.addInitializer(P2_INIT_ColorRandomRange(Vec3(255/255, 90/255, 90/255), Vec3(255/255, 126/255, 93/255)))
        else:
            system.addInitializer(P2_INIT_ColorRandomRange(Vec3(0/255, 159/255, 165/255), Vec3(116/255, 152/255, 255/255)))
        system.addInitializer(P2_INIT_ScaleRandomRange(Vec3(2), Vec3(2)))

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        l0 = ParticleLerpSegment()
        l0.type = l0.LTLinear
        l0.start = 0.0
        l0.end = 0.2
        l0.start_value = Vec3(0)
        l0.end_is_initial = True
        colorLerp.addSegment(l0)
        l0.start = 0.8
        l0.end = 1.0
        l0.start_is_initial = True
        l0.end_is_initial = False
        l0.end_value = Vec3(0)
        colorLerp.addSegment(l0)
        system.addFunction(colorLerp)

        system.addFunction(LifespanKillerParticleFunction(0.5))
        system.addFunction(LinearMotionParticleFunction())

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/healsign.mto")),
                                                ColorAttrib.makeVertex()))
        system.addRenderer(renderer)

        OverhealedEffect[team] = system

    return OverhealedEffect[team].makeCopy()

PlayerTeleportEffect = [None, None]
def getPlayerTeleportEffect(team):
    global PlayerTeleportEffect
    if not PlayerTeleportEffect[team]:
        from tf.tfbase import TFGlobals

        system = ParticleSystem2()
        system.setPoolSize(200)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(667)
        emitter.setDuration(0.5)
        system.addEmitter(emitter)

        system.addInitializer(P2_INIT_PositionModelHitBoxes(0))
        system.addInitializer(P2_INIT_LifespanRandomRange(4, 4))
        if team == TFGlobals.TFTeam.Red:
            system.addInitializer(P2_INIT_ColorRandomRange(Vec3(255/255, 90/255, 90/255), Vec3(255/255, 126/255, 93/255)))
        else:
            system.addInitializer(P2_INIT_ColorRandomRange(Vec3(0/255, 159/255, 165/255), Vec3(116/255, 152/255, 255/255)))
        system.addInitializer(P2_INIT_ScaleRandomRange(Vec3(1), Vec3(3), True))
        system.addInitializer(P2_INIT_RotationVelocityRandomRange(20, 35, True))

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        l0 = ParticleLerpSegment()
        l0.type = l0.LTLinear
        l0.start = 0.0
        l0.end = 0.05
        l0.start_value = Vec3(0)
        l0.end_is_initial = True
        colorLerp.addSegment(l0)
        l0.start = 0.8
        l0.end = 1.0
        l0.start_is_initial = True
        l0.end_is_initial = False
        l0.end_value = Vec3(0)
        colorLerp.addSegment(l0)
        system.addFunction(colorLerp)

        scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
        l0 = ParticleLerpSegment()
        l0.start = 0.0
        l0.end = 0.05
        l0.scale_on_initial = True
        l0.start_value = Vec3(0.3)
        l0.end_value = Vec3(2.5)
        l0.type = l0.LTLinear
        scaleLerp.addSegment(l0)
        l0.start_value = Vec3(2.5)
        l0.end_value = Vec3(1.0)
        l0.start = 0.05
        l0.end = 0.1
        scaleLerp.addSegment(l0)
        l0.scale_on_initial = False
        l0.start_is_initial = True
        l0.end_value = Vec3(0.3)
        l0.start = 0.1
        l0.end = 1.0
        scaleLerp.addSegment(l0)
        system.addFunction(scaleLerp)

        system.addFunction(LifespanKillerParticleFunction())
        system.addFunction(VelocityJitterParticleFunction(0.05, 0.05, Vec3(1, 1, 1), 0.1, 0.45))
        #system.addFunction(VelocityJitterParticleFunction(1, 1, Vec3(1, 1, 1), 0.48, 1.0))

        #system.addForce(VectorParticleForce(Vec3.up() * 4, 0.0, 0.5))
        system.addForce(VectorParticleForce(Vec3.down() * (200), 0.45))

        renderer = SpriteParticleRenderer2()
        renderer.setRenderState(RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/tp_spark.mto")),
                                                ColorAttrib.makeVertex()))
        system.addRenderer(renderer)

        PlayerTeleportEffect[team] = system

    return PlayerTeleportEffect[team].makeCopy()

MedigunHealBeam = [None, None]
def getMedigunHealBeam(team):
    global MedigunHealBeam
    if not MedigunHealBeam[team]:
        from tf.tfbase.TFGlobals import TFTeam

        sys = ParticleSystem2()
        sys.setPoolSize(166)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(150)
        sys.addEmitter(emitter)

        sys.addInitializer(P2_INIT_PositionSphereVolume((0, 0, 0), 0.1, 0.1, Vec3(1, 0, 1)))
        sys.addInitializer(P2_INIT_LifespanRandomRange(1, 1))
        sys.addInitializer(P2_INIT_ScaleRandomRange(Vec3(6), Vec3(6)))
        if team == TFTeam.Red:
            sys.addInitializer(P2_INIT_ColorRandomRange(Vec3(255/255, 90/255, 90/255), Vec3(255/255, 126/255, 93/255)))
        else:
            sys.addInitializer(P2_INIT_ColorRandomRange(Vec3(0/255, 159/255, 165/255), Vec3(116/255, 152/255, 255/255)))
        sys.addInitializer(P2_INIT_RotationVelocityRandomRange(96, 96))

        scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
        l0 = ParticleLerpSegment()
        l0.type = l0.LTLinear
        l0.start = 0.0
        l0.end = 1.0
        l0.start_is_initial = True
        l0.end_value = Vec3(1.0)
        scaleLerp.addSegment(l0)
        sys.addFunction(scaleLerp)

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        l0 = ParticleLerpSegment()
        l0.type = l0.LTLinear
        l0.start = 0.0
        l0.end = 1.0
        l0.start_is_initial = True
        if team == TFTeam.Red:
            l0.end_value = Vec3(255/255, 90/255, 0/255)
        else:
            l0.end_value = Vec3(48/255, 141/255, 255/255)
        colorLerp.addSegment(l0)
        sys.addFunction(colorLerp)

        sys.addFunction(LinearMotionParticleFunction())
        sys.addFunction(AngularMotionParticleFunction())
        sys.addFunction(LifespanKillerParticleFunction())

        twist = CylinderVortexParticleForce(512.0, (0, 1, 0))
        twist.setLocalAxis(False)
        twist.setInput0(0)
        twist.setInput1(1)
        twist.setMode(twist.AMVecBetweenInputs)
        sys.addForce(twist)

        const = PathParticleConstraint()
        const.start_input = 0
        const.end_input = 1
        const.max_distance = 2
        const.mid_point = 0.1
        const.min_distance = 2
        const.bulge_control = 1
        const.random_bulge = 1.3
        const.travel_time = 1.0
        sys.addConstraint(const)

        renderer = SpriteParticleRenderer2()
        state = RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/medicbeam_curl.mto")),
                        ColorAttrib.makeVertex())
        renderer.setRenderState(state)
        sys.addRenderer(renderer)

        MedigunHealBeam[team] = sys

    return MedigunHealBeam[team].makeCopy()

DispenserHealBeam = [None, None]
def getDispenserHealBeam(team):
    global DispenserHealBeam
    if not DispenserHealBeam[team]:
        from tf.tfbase.TFGlobals import TFTeam

        sys = ParticleSystem2()
        sys.setPoolSize(166)

        emitter = ContinuousParticleEmitter()
        emitter.setEmissionRate(150)
        sys.addEmitter(emitter)

        sys.addInitializer(P2_INIT_PositionSphereVolume((0, 0, 0), 0.1, 0.1, Vec3(1, 0, 1)))
        sys.addInitializer(P2_INIT_LifespanRandomRange(1, 1))
        sys.addInitializer(P2_INIT_ScaleRandomRange(Vec3(3), Vec3(3)))
        if team == TFTeam.Red:
            sys.addInitializer(P2_INIT_ColorRandomRange(Vec3(255/255, 90/255, 90/255), Vec3(255/255, 126/255, 93/255)))
        else:
            sys.addInitializer(P2_INIT_ColorRandomRange(Vec3(0/255, 159/255, 165/255), Vec3(116/255, 152/255, 255/255)))
        sys.addInitializer(P2_INIT_RotationVelocityRandomRange(96, 96))

        scaleLerp = LerpParticleFunction(LerpParticleFunction.CScale)
        l0 = ParticleLerpSegment()
        l0.type = l0.LTLinear
        l0.start = 0.0
        l0.end = 1.0
        l0.start_is_initial = True
        l0.end_value = Vec3(1.0)
        scaleLerp.addSegment(l0)
        sys.addFunction(scaleLerp)

        colorLerp = LerpParticleFunction(LerpParticleFunction.CRgb)
        l0 = ParticleLerpSegment()
        l0.type = l0.LTLinear
        l0.start = 0.0
        l0.end = 1.0
        l0.start_is_initial = True
        if team == TFTeam.Red:
            l0.end_value = Vec3(255/255, 90/255, 0/255)
        else:
            l0.end_value = Vec3(48/255, 141/255, 255/255)
        colorLerp.addSegment(l0)
        sys.addFunction(colorLerp)

        sys.addFunction(LinearMotionParticleFunction())
        sys.addFunction(AngularMotionParticleFunction())
        sys.addFunction(LifespanKillerParticleFunction())

        twist = CylinderVortexParticleForce(512.0, (0, 1, 0))
        twist.setLocalAxis(False)
        twist.setInput0(0)
        twist.setInput1(1)
        twist.setMode(twist.AMVecBetweenInputs)
        sys.addForce(twist)

        const = PathParticleConstraint()
        const.start_input = 0
        const.end_input = 1
        const.max_distance = 2
        const.mid_point = 0.1
        const.min_distance = 2
        const.bulge_control = 1
        const.random_bulge = 1.3
        const.travel_time = 1.0
        sys.addConstraint(const)

        renderer = SpriteParticleRenderer2()
        state = RenderState.make(MaterialAttrib.make(loader.loadMaterial("materials/medicbeam_curl.mto")),
                        ColorAttrib.makeVertex())
        renderer.setRenderState(state)
        sys.addRenderer(renderer)

        DispenserHealBeam[team] = sys

    return DispenserHealBeam[team].makeCopy()

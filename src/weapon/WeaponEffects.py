
from panda3d.core import *

from tf.tfbase import Sounds
from direct.interval.IntervalGlobal import Sequence, LerpFunc, Func
import random

def lerp(v0, v1, amt):
    return v0 * amt + v1 * (1 - amt)

class MuzzleParticle(NodePath):

    muzzleroot = "maps/starflash01.txo"

    def __init__(self, startSize, endSize, roll, color, duration):
        NodePath.__init__(self, 'muzzleParticle')

        cm = CardMaker("muzzleSpriteCard")
        cm.setFrame(-1, 1, -1, 1)
        cm.setHasUvs(True)
        cm.setUvRange((0, 0), (1, 1))
        cmnp = self.attachNewNode(cm.generate())
        cmnp.setBillboardAxis()

        self.setTexture(loader.loadTexture(self.muzzleroot), 1)
        #self.setShaderOff(1)
        self.setLightOff(1)
        self.setMaterialOff(1)
        self.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OOne, ColorBlendAttrib.OOne), 1)
        self.setDepthWrite(False, 1)
        self.setBin('fixed', 0, 1)
        #self.setTransparency(1)

        self.startAlpha = 0.5
        self.endAlpha = 0.0
        self.duration = duration
        self.startSize = startSize
        self.endSize = endSize
        self.color = color
        self.startTime = base.getRenderTime()
        self.roll = roll
        taskMgr.add(self.particleUpdate, "muzzleParticleUpdate-" + str(id(self)))

    def removeNode(self):
        taskMgr.remove("muzzleParticleUpdate-" + str(id(self)))
        del self.startAlpha
        del self.endAlpha
        del self.duration
        del self.startSize
        del self.endSize
        del self.color
        del self.startTime
        del self.roll
        NodePath.removeNode(self)

    def particleUpdate(self, task):
        deltaTime = globalClock.frame_time - self.startTime
        timeFraction = deltaTime / self.duration
        if timeFraction >= 1.0:
            self.removeNode()
            return task.done

        alpha = lerp(self.endAlpha, self.startAlpha, timeFraction)
        size = lerp(self.endSize, self.startSize, timeFraction)

        self.setScale(size)
        self.setR(self.roll)
        self.setColorScale(self.color[0] * alpha, self.color[1] * alpha, self.color[2] * alpha, alpha, 1)

        return task.cont

def makeMuzzleFlash(node, pos, hpr, scale, color = (1, 1, 1, 1), viewModel=False):
    from tf.tfbase import TFEffects
    from direct.interval.IntervalGlobal import Sequence, Wait, Func
    saveTime = globalClock.frame_time
    base.setFrameTime(base.getRenderTime())
    effect = TFEffects.getMuzzleFlashEffect(viewModel)
    effect.setInput(0, node, False)
    effect.start(node)
    Sequence(Wait(0.1), Func(effect.softStop)).start()
    base.setFrameTime(saveTime)

    cje = None
    if node.hasEffect(CharacterJointEffect.getClassType()):
        cje = node.getEffect(CharacterJointEffect.getClassType())
        node.clearEffect(CharacterJointEffect.getClassType())
    l = qpLight(qpLight.TPoint)
    l.setColorSrgb((1 * 1.5, 0.9 * 1.5, 0.5 * 1.5))
    l.setAttenuation(1, 0, 0.001)
    l.setAttenuationRadius(128)
    pos = node.getPos(base.render)
    if viewModel:
        pos = base.localAvatar.viewModel.calcViewModelAttachmentPos(pos)
    l.setPos(pos)
    base.addDynamicLight(l, fadeTime=0.15, followParent=node)
    if cje:
        node.setEffect(cje)

    """
    import random
    from panda3d.core import Quat, Point3
    quat = Quat()
    quat.setHpr(hpr)
    forward = quat.getForward()

    #scale = random.uniform(scale-0.25, scale+0.25)
    #scale = clamp(scale, 0.5, 8.0)

    for i in range(1, 9):
        offset = Point3(pos) + (forward * (i*(2)*scale))
        size = (random.uniform(6, 9) * (12-(i))/9) * scale
        roll = random.randint(0, 360)
        dur = 0.2
        p = MuzzleParticle(size, size, roll, color, dur)
        p.reparentTo(node)
        p.setPos(offset)
        p.setHpr(hpr)
    """

def intersectRayWithRay(start1, end1, start2, end2):

    v0 = end1 - start1
    v1 = end2 - start2
    v0.normalize()
    v1.normalize()

    v0xv1 = v0.cross(v1)
    lengthSq = v0xv1.lengthSquared()

    if lengthSq == 0.0:
        return (False, 0.0, 0.0) # Parallel

    p1p0 = start2 - start1

    AxC = -p1p0.cross(v0xv1)
    detT = AxC.dot(v1)
    detS = AxC.dot(v0)

    t = detT / lengthSq
    s = detS / lengthSq

    # Intersection?
    i0 = v0 * t
    i1 = v1 * s
    i0 += start1
    i1 += start2

    if i0.almostEqual(i1):
        return (True, s, t)

    return (False, s, t)

def calcClosestPointToLineT(P, lineA, lineB, dir):
    dir.set(lineB.x - lineA.x,
            lineB.y - lineA.y,
            lineB.z - lineA.z)

    div = dir.dot(dir)
    if div < 0.00001:
        return 0

    return (dir.dot(P) - dir.dot(lineA)) / div

def calcClosestPointOnLineSegment(P, lineA, lineB):
    dir = Vec3()
    t = calcClosestPointToLineT(P, lineA, lineB, dir)
    t = max(0.0, min(1.0, t))
    return lineA + dir * t

def calcDistanceSqrToLineSegment(P, lineA, lineB):
    closest = calcClosestPointOnLineSegment(P, lineA, lineB)
    return ((P - closest).lengthSquared(), closest)

class Whiz:

    def __init__(self, snd, start, end):
        length = snd.length()
        self.snd = snd
        self.start = start
        self.end = end
        self.delta = end - start
        ival = Sequence(LerpFunc(self.__update, length), Func(self.cleanup))
        ival.start()

    def cleanup(self):
        self.snd = None
        self.start = None
        self.end = None
        self.delta = None

    def __update(self, t):
        point = self.start + self.delta * t
        self.snd.set3dAttributes(point, Quat.identQuat(), Vec3())

nextWhizTime = 0.0
def tracerSound(start, end):
    global nextWhizTime

    #print("tracer sound")

    dt = nextWhizTime - globalClock.frame_time
    #print("Dt", dt)
    if dt > 0:
        return

    #print("start", start, "end", end)
    #print("len", (start-end).length())

    if (start - end).length() < 200.0:
        return

    soundName = "Bullets.DefaultNearmiss"
    whizDist = 96
    listenOrigin = base.cam.getPos(base.render)

    lower = Point3(listenOrigin)
    lower.z -= 24.0

    ret, s, t = intersectRayWithRay(start, end, listenOrigin, lower)
    t = max(0.0, min(1.0, t))
    listenOrigin.z -= t * 24.0

    #print("listen origin", listenOrigin, "cam pos", base.cam.getPos(base.render))

    dist, point = calcDistanceSqrToLineSegment(listenOrigin, start, end)
    #print("dist", dist, "point", point)
    if dist >= whizDist*whizDist:
        #print("too far")
        return
    elif dist <= 0.0:
        return

    nextWhizTime = globalClock.frame_time + 0.1

    snd = Sounds.createSoundByName(soundName, spatial=True)
    #snd.set3dDistanceFactor(0.0)
    snd.set3dMinDistance(10000000.0)
    snd.set3dAttributes(start, Quat.identQuat(), Vec3())
    snd.play()

    dir = (end - start).normalized()
    w = Whiz(snd, point - (dir * 512), point + (dir * 512))

    #snd = base.world.emitSoundSpatial(soundName, point)
    #snd.set3dDistanceFactor(0.0)
    #print("snd", snd)

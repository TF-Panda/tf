
from panda3d.core import NodePath, CardMaker, ColorBlendAttrib

import random

def lerp(v0, v1, amt):
    return v0 * amt + v1 * (1 - amt)

class MuzzleParticle(NodePath):

    muzzleroot = "tfmodels/src/maps/starflash01.tga"

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
        #self.setTransparency(1)

        self.startAlpha = 0.5
        self.endAlpha = 0.0
        self.duration = duration
        self.startSize = startSize
        self.endSize = endSize
        self.color = color
        self.startTime = globalClock.getFrameTime()
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
        deltaTime = globalClock.getFrameTime() - self.startTime
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

def makeMuzzleFlash(node, pos, hpr, scale, color = (1, 1, 1, 1)):
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

"""FogManager module: contains the FogManager class."""

from direct.showbase.DirectObject import DirectObject

from panda3d.core import *

class FogManager(DirectObject):

    def __init__(self):
        self.fogStart = 0
        self.fogEnd = 100
        self.color = Vec4(1)
        self.color2 = Vec4(1)
        self.fogDir = Vec3.forward()
        self.fogBlend = False
        self.fogMaxDensity = 1
        self.fogNode = Fog('fog')
        self.enabled = False

    def enableFog(self):
        self.enabled = True
        render.setFog(self.fogNode)
        taskMgr.add(self.__updateFog, 'updateFog', sort = 40)

    def disableFog(self):
        self.enabled = False
        render.clearFog(self.fogNode)
        taskMgr.remove('updateFog')

    def __updateFog(self, task):
        self.updateParams()
        return task.cont

    def updateParams(self):
        # Updates the fog blending params.
        self.fogNode.setLinearRange(self.fogStart, self.fogEnd)
        if self.fogBlend:
            q = base.camera.getQuat(render)
            fwd = q.getForward()
            blendFactor = 0.5 * fwd.dot(self.fogDir) + 0.5
            blendColor = self.color * blendFactor + self.color2 * (1 - blendFactor)
            self.fogNode.setColor(blendColor)
        else:
            self.fogNode.setColor(self.color)




"""FogManager module: contains the FogManager class."""

from panda3d.core import *

from direct.showbase.DirectObject import DirectObject


class FogManager(DirectObject):

    def __init__(self, scene):
        self.scene = scene
        self.fogStart = 0
        self.fogEnd = 100
        self.color = Vec4(1)
        self.color2 = Vec4(1)
        self.fogDir = Vec3.forward()
        self.fogBlend = False
        self.fogMaxDensity = 1
        self.fogNode = Fog('fog')
        self.enabled = False
        self.task = None

    def cleanup(self):
        if self.enabled:
            self.disableFog()
        self.fogNode = None
        self.scene = None

    def enableFog(self):
        self.enabled = True
        self.scene.setFog(self.fogNode)
        self.task = taskMgr.add(self.__updateFog, 'updateFog', sort = 40)

    def disableFog(self):
        self.enabled = False
        if self.scene:
            self.scene.clearFog()
        if self.task:
            self.task.remove()
            self.task = None

    def __updateFog(self, task):
        self.updateParams()
        return task.cont

    def updateParams(self):
        # Updates the fog blending params.
        #print(self.fogStart, self.fogEnd, self.fogBlend)
        self.fogNode.setLinearRange(self.fogStart, self.fogEnd)
        if self.fogBlend:
            q = base.camera.getQuat(render)
            fwd = q.getForward()
            blendFactor = 0.5 * fwd.dot(self.fogDir) + 0.5
            blendColor = self.color * blendFactor + self.color2 * (1 - blendFactor)
            self.fogNode.setColor(blendColor)
            #print("blend color", blendColor)
        else:
            self.fogNode.setColor(self.color)
            #print("color", self.color)




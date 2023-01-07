"""TeamControlPointMaster module: contains the TeamControlPointMaster class."""

from direct.distributed2.DistributedObject import DistributedObject

from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from panda3d.core import *

from tf.tfbase import TFGlobals

class ControlPointWidget(DirectObject):

    def __init__(self, point, panel, pos):
        self.point = point
        self.bar = DirectWaitBar(frameSize=(-0.08, 0.08, -0.08, 0.08),
                                 range=1.0, value=0.0, text_scale=0.04, text_pos=(0, 0),
                                 parent=panel.frame, pos=pos, text="")

        #self.accept('ControlPointOwnerTeamChanged', self.__handlePointUpdate)
        self.accept('ControlPointProgressChanged', self.__handlePointUpdate)

        self.updateBar()

    def __handlePointUpdate(self, point):
        if point != self.point:
            return
        self.updateBar()

    def updateBar(self):
        if self.point.defaultOwner == TFGlobals.TFTeam.Red:
            self.bar['frameColor'] = (0.9, 0.5, 0.5, 1.0)
            self.bar['barColor'] = (0.5, 0.65, 1, 1.0)
        else:
            self.bar['frameColor'] = (0.5, 0.65, 1, 1.0)
            self.bar['barColor'] = (0.9, 0.5, 0.5, 1.0)
        self.bar['value'] = self.point.capProgress

    def cleanup(self):
        self.ignoreAll()
        self.point = None
        self.bar.destroy()
        self.bar = None

class ControlPointGuiPanel:

    canvasMins = Vec2(-0.4, -0.2)
    canvasMaxs = Vec2(0.4, 0.2)
    canvasSize = canvasMaxs - canvasMins

    def __init__(self, master):
        self.master = master
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0.75), relief=DGG.FLAT,
                                 frameSize=(self.canvasMins[0] - 0.02, self.canvasMaxs[0] + 0.02,
                                            self.canvasMins[1] - 0.02, self.canvasMaxs[1] + 0.02),
                                 parent=base.a2dBottomCenter, pos=(0, 0, 0.225), scale=0.8)
        # By point DoId.
        self.pointWidgets = {}

    def destroyWidgets(self):
        if not self.pointWidgets:
            return
        for w in self.pointWidgets.values():
            w.cleanup()
        self.pointWidgets = {}

    def destroy(self):
        self.destroyWidgets()
        self.pointWidgets = None
        self.frame.destroy()
        self.frame = None
        self.master = None

    def create(self):
        self.destroyWidgets()

        layout = self.master.pointLayout
        layout2D = []
        currRow = []
        for i in layout:
            if i == -1:
                layout2D.append(currRow)
                currRow = []
            else:
                currRow.append(i)
        if currRow:
            layout2D.append(currRow)

        numRows = len(layout2D)
        ySize = self.canvasSize.y / numRows
        for i in range(numRows):
            yMin = self.canvasMaxs.y - ySize * (i + 1)
            numCols = len(layout2D[i])
            xSize = self.canvasSize.x / numCols
            for j in range(numCols):
                xMin = self.canvasMaxs.x - xSize * (j + 1)

                xPos = xMin + xSize * 0.5
                yPos = yMin + ySize * 0.5

                pointDoId = self.master.pointDoIds[layout2D[i][j]]
                point = base.cr.doId2do.get(pointDoId)

                w = ControlPointWidget(point, self, (xPos, 0, yPos))
                self.pointWidgets[point] = w

class TeamControlPointMaster(DistributedObject):

    def __init__(self):
        DistributedObject.__init__(self)
        self.panel = None
        self.pointLayout = []
        self.pointDoIds = []

    def generate(self):
        DistributedObject.generate(self)
        self.panel = ControlPointGuiPanel(self)

    def postDataUpdate(self):
        DistributedObject.postDataUpdate(self)
        if self.pointLayout and self.pointDoIds:
            self.panel.create()

    def delete(self):
        self.panel.destroy()
        self.panel = None
        DistributedObject.delete(self)

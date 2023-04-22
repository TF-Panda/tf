"""TeamControlPointMaster module: contains the TeamControlPointMaster class."""

from direct.distributed2.DistributedObject import DistributedObject

from . import CapState

from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import Sequence, LerpFunc
from panda3d.core import *

from tf.tfbase import TFGlobals
from tf.tfgui import TFGuiProperties

class ControlPointWidget(DirectObject):

    BlinkScale = 1.3
    BlinkTime = 0.5

    def __init__(self, point, panel, pos):
        self.point = point
        self.bar = DirectWaitBar(frameSize=(-0.08, 0.08, -0.08, 0.08),
                                 range=1.0, value=0.0, text_scale=0.05, text_pos=(0, 0), text_fg=TFGuiProperties.TextColorLight,
                                 text_shadow=TFGuiProperties.TextShadowColor,
                                 text_align=TextNode.ACenter,
                                 parent=panel.frame, pos=pos, text="", text_font=TFGlobals.getTF2SecondaryFont(),
                                 )

        #self.accept('ControlPointOwnerTeamChanged', self.__handlePointUpdate)
        self.accept('ControlPointProgressChanged', self.__handlePointUpdate)
        self.accept('ControlPointCapperCountChanged', self.__handlePointUpdate)

        self.blinkIval = None

        self.updateBar()

    def __handlePointUpdate(self, point):
        if point != self.point:
            return
        self.updateBar()

    def getTeamBarColor(self):
        if self.point.defaultOwner == TFGlobals.TFTeam.Red:
            return TFGuiProperties.BackgroundColorBlueOpaque
        else:
            return TFGuiProperties.BackgroundColorRedOpaque

    def updateBar(self):
        # Updates the UI state of the capture point widget based on the
        # state of the associated capture point.

        if self.point.defaultOwner == TFGlobals.TFTeam.Red:
            self.bar['frameColor'] = TFGuiProperties.BackgroundColorRedTranslucent
        else:
            self.bar['frameColor'] = TFGuiProperties.BackgroundColorBlueTranslucent

        self.bar['barColor'] = self.getTeamBarColor()

        self.bar['value'] = self.point.capProgress

        # Update bar text to show what is happening.
        if self.point.capState == CapState.CSCapping and self.point.capperCount > 0:
            # Show capper count when capping.
            self.bar['text'] = f'x{self.point.capperCount}'
        elif self.point.capState == CapState.CSBlocked:
            self.bar['text'] = '>><<' # Dunno
        elif self.point.capState == CapState.CSReverting and self.point.capperCount > 0:
            # Number of players reversing the cap.
            self.bar['text'] = f'x{self.point.capperCount}'
        else:
            self.bar['text'] = ''

        if self.point.capState != CapState.CSIdle:
            # Something interesting is happening to the point, so pulse the bar.
            self.startBlink()
        else:
            self.stopBlink()

    def startBlink(self):

        # Starts the blinking interval on the progress bar for this capture point
        # while it is not idle (being captured, reverted, blocked, etc).

        def lerpTheBarColor(t):
            # Scale up the bar color to pulse it.
            col = Vec4(self.getTeamBarColor())
            origA = float(col[3])
            col = (col * (1 - t)) + (col * self.BlinkScale * t)
            col[3] = origA
            self.bar['barColor'] = col

        if not self.blinkIval:
            self.blinkIval = Sequence(LerpFunc(lerpTheBarColor, fromData=0, toData=1, duration=self.BlinkTime, blendType='easeInOut'),
                                      LerpFunc(lerpTheBarColor, fromData=1, toData=0, duration=self.BlinkTime, blendType='easeInOut'))
            self.blinkIval.loop()

    def stopBlink(self):
        if self.blinkIval:
            self.blinkIval.finish()
            self.blinkIval = None
        self.bar['barColor'] = self.getTeamBarColor()

    def cleanup(self):
        self.ignoreAll()
        self.stopBlink()
        self.point = None
        self.bar.destroy()
        self.bar = None

class ControlPointGuiPanel:

    canvasMins = Vec2(-0.4, -0.2)
    canvasMaxs = Vec2(0.4, 0.2)
    canvasSize = canvasMaxs - canvasMins

    def __init__(self, master):
        self.master = master
        self.frame = DirectFrame(frameColor=TFGuiProperties.BackgroundColorNeutralTranslucent, relief=DGG.FLAT,
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

        # Create widgets for each capture point in the round.
        # Lay them out in a grid.

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

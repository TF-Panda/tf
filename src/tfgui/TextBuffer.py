"""TextBuffer module: contains the TextBuffer class."""

from panda3d.core import *

from direct.gui.DirectGui import *
from tf.tfbase import TFGlobals

class BufferLabel:

    def __init__(self, label, buf):
        self.buf = buf
        self.label = label
        self.label.setTransparency(True)
        self.createTime = globalClock.frame_time

    def setLabelAlpha(self, alpha):
        self.label.setAlphaScale(alpha, 1)

    def clearLabelAlpha(self, alpha):
        self.label.clearAlphaScale()

class TextBuffer:

    def __init__(self, dimensions=(-1, 1, 0.25, 1), parent=base.aspect2d, width=30,
                 maxBufLines=100, rootScale=1.0, enterCallback=None, font=None, scrollBarWidth=0.04, margin=0.1,
                 textColor=(1, 1, 1, 1), bgAlpha=0.8, entryAlpha=0.9):
        # Dimensions. L R B T.  Includes the entry.
        self.dimensions = dimensions
        self.maxBufLines = maxBufLines

        self.textColor = textColor

        self.font = font

        self.enterCallback = enterCallback

        self.scrollBarWidth = scrollBarWidth

        self.isOpen = False

        # Chat labels.
        self.labels = []

        self.root = parent.attachNewNode("textBuffer")
        self.root.setScale(rootScale)
        self.root.setTransparency(True)

        margin = 0.1
        self.margin = margin
        self.entry = DirectEntry(frameColor = (0.05, 0.05, 0.05, entryAlpha), initialText="", text_font=font,
                                 relief=DGG.FLAT, width=width, parent=self.root, overflow=0, command=self.onEnter,
                                 text_fg=textColor, text_shadow=(0, 0, 0, 1), suppressKeys=1, suppressMouse=1)

        self.wordWrapObj = TextNode('wordWrapObj')
        self.wordWrapObj.setAlign(TextNode.ALeft)

        canvasDim = (self.dimensions[0], self.dimensions[1] - scrollBarWidth, self.dimensions[2], self.dimensions[3])
        self.scrollFrame = DirectScrolledFrame(frameSize=self.dimensions, canvasSize=canvasDim, frameColor=(0.1, 0.1, 0.1, bgAlpha),
                                               parent=self.root, relief=DGG.FLAT, scrollBarWidth=scrollBarWidth,
                                               verticalScroll_thumb_relief=DGG.FLAT, verticalScroll_incButton_relief=DGG.FLAT,
                                               verticalScroll_decButton_relief=DGG.FLAT,
                                               verticalScroll_thumb_frameColor=((0.4, 0.4, 0.4, 1), (0.25, 0.25, 0.25, 1), (0.75, 0.75, 0.75, 1)),
                                               verticalScroll_incButton_frameColor=((0.45, 0.45, 0.45, 1), (0.25, 0.25, 0.25, 1), (0.75, 0.75, 0.75, 1)),
                                               verticalScroll_decButton_frameColor=((0.45, 0.45, 0.45, 1), (0.25, 0.25, 0.25, 1), (0.75, 0.75, 0.75, 1)))

        self.adjustTextWidth(width)

        self.fadeTask = None
        self.fadeInSpeed = 5.0 # 0.2 seconds
        self.fadeOutSpeed = 5.0 # 0.2 seconds
        self.alpha = 0.0
        self.goalAlpha = 0.0

        self.root.hide()

    def cleanup(self):
        for lbl in self.labels:
            lbl.cleanup()
        del self.labels
        self.entry.destroy()
        del self.entry
        self.wordWrapObj = None
        self.stopFadeTask()
        self.scrollFrame.destroy()
        del self.scrollFrame
        self.root.removeNode()
        del self.root
        del self.font

    def adjustTextWidth(self, width):
        self.width = width
        scale = (self.dimensions[1] - self.dimensions[0]) / (width + (self.margin * 2))
        self.scale = scale
        self.labelRootPos = (self.dimensions[0] + self.margin * self.scale, self.dimensions[3] - (self.wordWrapObj.getLineHeight() * 0.75 * self.scale))
        self.entry['width'] = width
        self.entry.setScale(self.scale)
        self.entry.setPos(0, 0, 0)
        self.entry.setFrameSize()
        bounds = self.entry.getBounds()
        self.entry.setPos(self.dimensions[0] + (self.margin * self.scale), 0, self.dimensions[2] - bounds[3] * self.scale)
        self.positionLabels()

    def setGoalAlpha(self, fade):
        if self.alpha != fade:
            self.goalAlpha = fade
            self.startFadeTask()

    def setAlpha(self, alpha):
        self.alpha = self.goalAlpha = alpha
        self.root.setColorScale(1, 1, 1, alpha)

    def startFadeTask(self):
        self.stopFadeTask()
        self.fadeTask = base.taskMgr.add(self.__update, 'updateTextBuffer')

    def stopFadeTask(self):
        if self.fadeTask:
            self.fadeTask.remove()
            self.fadeTask = None

    def setFadeInTime(self, time):
        self.fadeInSpeed = 1.0 / time

    def setFadeOutTime(self, time):
        self.fadeOutSpeed = 1.0 / time

    def __update(self, task):
        if self.alpha != self.goalAlpha:
            if self.alpha > self.goalAlpha:
                # Fade out.
                self.alpha = TFGlobals.approach(self.goalAlpha, self.alpha, self.fadeOutSpeed * globalClock.dt)
                if self.alpha == self.goalAlpha:
                    self.root.hide()
            else:
                # Fade in.
                self.alpha = TFGlobals.approach(self.goalAlpha, self.alpha, self.fadeInSpeed * globalClock.dt)

            self.root.setColorScale(1, 1, 1, self.alpha)
            return task.cont
        return task.done

    def open(self, fade=True):
        self.entry.set('')
        self.entry['focus'] = 1

        self.root.show()

        if fade:
            self.setGoalAlpha(1.0)
        else:
            self.setAlpha(1.0)

        self.isOpen = True

        self.positionLabels()

    def close(self, fade=True):
        if fade:
            self.setGoalAlpha(0.0)
        else:
            self.setAlpha(0.0)
            self.root.hide()
        self.isOpen = False

        self.positionLabels()

    def getWordwrap(self):
        if self.isOpen:
            return self.width - (self.scrollBarWidth / self.scale)
        else:
            return self.width

    def positionLabels(self):
        self.labelZOffset = 0.0
        ww = self.getWordwrap()
        self.wordWrapObj.setWordwrap(ww)
        for lbl in self.labels:
            lbl.setTextPos(self.labelRootPos[0], self.labelRootPos[1] - self.labelZOffset)
            lbl.setWordwrap(ww)
            lbl.setTextScale(self.scale)
            wrapped = lbl.textNode.getWordwrappedText().split('\n')
            self.labelZOffset += len(wrapped) * lbl.textNode.getLineHeight() * self.scale
        self.__updateText()

    def addLine(self, line):
        self.wordWrapObj.setText(line)

        labelPos = (self.labelRootPos[0], self.labelRootPos[1] - self.labelZOffset)
        label = OnscreenText(line, parent=self.scrollFrame.getCanvas(), wordwrap=self.wordWrapObj.getWordwrap(), scale=self.scale, font=self.font,
                             align=TextNode.ALeft, fg=self.textColor, shadow=(0, 0, 0, 1),
                             pos=labelPos, mayChange=True)

        result = self.wordWrapObj.getWordwrappedText().split('\n')
        self.labelZOffset += len(result) * self.wordWrapObj.getLineHeight() * self.scale
        self.labels.append(label)

        self.__updateText()

        return BufferLabel(label, self)

    def __updateText(self):

        buffOffset = self.labelZOffset + self.wordWrapObj.getLineHeight() * 0.25 * self.scale

        scrollSize = (self.dimensions[0], self.dimensions[1] - self.scrollBarWidth, min(self.dimensions[2], self.dimensions[3] - buffOffset),
                      self.dimensions[3])
        self.scrollFrame['canvasSize'] = scrollSize
        self.scrollFrame.verticalScroll.setValue(1.0)

    def onEnter(self, txt):
        self.entry.set('')
        self.entry['focus'] = 1
        if self.enterCallback:
            self.enterCallback(txt)

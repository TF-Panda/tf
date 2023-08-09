"""TextBuffer module: contains the TextBuffer class."""

from panda3d.core import *

from direct.gui.DirectGui import *
from tf.tfbase import TFGlobals


class TextBuffer:

    def __init__(self, dimensions=(-1, 1, 0.25, 1), parent=base.aspect2d, width=30,
                 maxBufLines=100, rootScale=1.0, enterCallback=None, font=None, scrollBarWidth=0.04, margin=0.1,
                 textColor=(1, 1, 1, 1)):
        # Dimensions. L R B T.  Includes the entry.
        self.dimensions = dimensions
        self.maxBufLines = maxBufLines

        self.enterCallback = enterCallback

        self.scrollBarWidth = scrollBarWidth

        self.width = width
        # Because the scroll bar is inside the scroll frame, it covers up the text if it
        # actually extends the entire width of the frame, so we need to wrap the
        # text before the scroll bar.
        adjustedWidth = width - scrollBarWidth

        self.lines = []

        self.root = parent.attachNewNode("textBuffer")
        self.root.setScale(rootScale)
        self.root.setTransparency(True)

        margin = 0.1
        # Calculate scale to fit the entry to the text buffer dimensions.
        scale = (self.dimensions[1] - self.dimensions[0]) / (width + (margin * 2))
        self.scale = scale
        self.entry = DirectEntry(frameColor = (0, 0, 0, 0.75), initialText="", text_font=font,
                                 relief=DGG.FLAT, width=width, scale=scale, parent=self.root, overflow=0, command=self.onEnter,
                                 text_fg=textColor, text_shadow=(0, 0, 0, 1), suppressKeys=1, suppressMouse=1)
        # Proper height placement.  Calculate the height of the entry.
        bounds = self.entry.getBounds()
        # Place the entry at the bottom left corner of the buffer frame.
        self.entry.setPos(self.dimensions[0] + (margin * scale), 0, self.dimensions[2] - bounds[3] * scale)

        self.wordWrapObj = TextNode('wordWrapObj')
        self.wordWrapObj.setWordwrap(adjustedWidth)

        self.bufferText = OnscreenText('', parent=self.root, wordwrap=adjustedWidth, scale=scale, font=font,
                                       align=TextNode.ALeft, fg=textColor, shadow=(0, 0, 0, 1),
                                       pos=(self.dimensions[0] + margin * scale, self.dimensions[3] - (self.wordWrapObj.getLineHeight() * scale * 0.5) - (margin * 2 * scale)))

        canvasDim = (self.dimensions[0], self.dimensions[1] - scrollBarWidth, self.dimensions[2], self.dimensions[3])
        self.scrollFrame = DirectScrolledFrame(frameSize=self.dimensions, canvasSize=canvasDim, frameColor=(0, 0, 0, 0.5),
                                               parent=self.root, relief=DGG.FLAT, scrollBarWidth=scrollBarWidth,
                                               verticalScroll_scrollSize=self.wordWrapObj.getLineHeight() * self.scale,
                                               verticalScroll_thumb_relief=DGG.FLAT, verticalScroll_incButton_relief=DGG.FLAT,
                                               verticalScroll_decButton_relief=DGG.FLAT,
                                               verticalScroll_thumb_frameColor=((0.4, 0.4, 0.4, 1), (0.25, 0.25, 0.25, 1), (0.75, 0.75, 0.75, 1)),
                                               verticalScroll_incButton_frameColor=((0.45, 0.45, 0.45, 1), (0.25, 0.25, 0.25, 1), (0.75, 0.75, 0.75, 1)),
                                               verticalScroll_decButton_frameColor=((0.45, 0.45, 0.45, 1), (0.25, 0.25, 0.25, 1), (0.75, 0.75, 0.75, 1)))

        self.bufferText.reparentTo(self.scrollFrame.getCanvas())

        self.fadeTask = None
        self.fadeInSpeed = 4.0 # 0.25 seconds
        self.fadeOutSpeed = 4.0 # 0.25 seconds
        self.alpha = 0.0
        self.goalAlpha = 0.0

        self.root.stash()

        self.isOpen = False

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
                    self.root.stash()
            else:
                # Fade in.
                self.alpha = TFGlobals.approach(self.goalAlpha, self.alpha, self.fadeInSpeed * globalClock.dt)

            self.root.setColorScale(1, 1, 1, self.alpha)
            return task.cont
        return task.done

    def open(self, fade=True):
        self.entry.set('')
        self.entry['focus'] = 1

        self.root.unstash()

        if fade:
            self.setGoalAlpha(1.0)
        else:
            self.setAlpha(1.0)

        self.isOpen = True

    def close(self, fade=True):
        if fade:
            self.setGoalAlpha(0.0)
        else:
            self.setAlpha(0.0)
            self.root.stash()
        self.isOpen = False

    def addLine(self, line):
        self.wordWrapObj.setText(line)
        result = self.wordWrapObj.getWordwrappedText().split('\n')
        self.lines += result
        self.__updateText()

    def __updateText(self):
        self.lines = self.lines[-self.maxBufLines:]
        self.bufferText['text'] = '\n'.join(self.lines)
        bufHeight = (self.wordWrapObj.getLineHeight() * self.scale * len(self.lines))

        scrollSize = (self.dimensions[0], self.dimensions[1] - self.scrollBarWidth, min(self.dimensions[2], self.dimensions[3] - bufHeight),
                      self.dimensions[3])
        self.scrollFrame['canvasSize'] = scrollSize
        self.scrollFrame.verticalScroll.setValue(1.0)

    def onEnter(self, txt):
        self.entry.set('')
        self.entry['focus'] = 1
        if self.enterCallback:
            self.enterCallback(txt)

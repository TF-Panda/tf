"""DamageNumbers module: contains the DamageNumbers class."""

from panda3d.core import Point2, TextNode

from direct.interval.IntervalGlobal import (LerpColorScaleInterval, Sequence,
                                            Wait)
from direct.showbase.DirectObject import DirectObject
from tf.tfbase import TFGlobals


class DamageText:

    def __init__(self, textNp, track, doneEvent):
        self.textNp = textNp
        self.track = track
        self.doneEvent = doneEvent
        self.upMove = 0.0

    def cleanup(self):
        self.track.finish()
        self.track = None
        self.textNp.removeNode()
        self.textNp = None
        self.doneEvent = None
        self.task.remove()
        self.task = None

class DamageNumbers(DirectObject):
    """
    Manages text above players showing damage the local avatar recently
    dealt.
    """

    def __init__(self):
        self.texts = set()

    def addDamage(self, amount, pos):
        if amount == 0:
            return

        # Create some text.
        text = TextNode('damageText')
        text.setText('-' + str(amount))
        text.setFont(TFGlobals.getTF2Font())
        text.setTextColor(1, 0, 0, 1)
        text.setAlign(TextNode.ACenter)
        text.setTextScale(0.065)
        textNp = base.render2d.attachNewNode(text.generate())
        textNp.setTransparency(True)
        textNp.setScale(0.075)

        track = Sequence(
            LerpColorScaleInterval(textNp, 0.2, (1, 1, 1, 1), (1, 1, 1, 0)),
            Wait(0.6),
            LerpColorScaleInterval(textNp, 0.2, (1, 1, 1, 0), (1, 1, 1, 1))
        )

        doneEvent = "dmgNumberTrackDone-" + str(id(text))
        track.setDoneEvent(doneEvent)

        dmgText = DamageText(textNp, track, doneEvent)
        dmgText.pos3d = pos
        dmgText.task = base.taskMgr.add(self.updateDmgText, 'updateDmgText-' + str(id(text)), extraArgs=[dmgText], appendTask=True, sort=49)
        self.acceptOnce(doneEvent, self.onTrackDone, extraArgs=[dmgText])
        self.texts.add(dmgText)

        self.calcDmgTextPos(dmgText)

        track.start()

    def calcDmgTextPos(self, dmgText):
        viewPos = base.cam.getRelativePoint(base.render, dmgText.pos3d)
        pos2d = Point2()
        base.camLens.project(viewPos, pos2d)
        ratio = base.camLens.getAspectRatio()
        if ratio < 1:
            dmgText.textNp.setScale(1.0, ratio, ratio)
        else:
            dmgText.textNp.setScale(1.0 / ratio, 1.0, 1.0)
        dmgText.textNp.setPos(pos2d.x, 0, pos2d.y)

    def updateDmgText(self, dmgText, task):
        self.calcDmgTextPos(dmgText)
        dmgText.upMove += 0.05 * base.clockMgr.getDeltaTime()
        dmgText.textNp.setZ(dmgText.textNp.getZ() + dmgText.upMove)
        return task.cont

    def onTrackDone(self, dmgText):
        if dmgText in self.texts:
            self.texts.remove(dmgText)

        dmgText.cleanup()

    def cleanup(self):
        for text in self.texts:
            self.ignore(text.doneEvent)
            text.cleanup()
        self.texts = None


"""Eyes module: contains the Eyes class."""

import random

from panda3d.core import *

from direct.interval.IntervalGlobal import *


class Eyes:
    """
    Handles eye movement and blinking for a character that has eyes.
    """

    def __init__(self, characterNp, debug=False):
        # Set this to correct the rotation of a head joint whose rotation
        # is not exactly center.
        self.headRotationOffset = Vec3(0, -80, 0)

        self.charNp = characterNp
        self.char = self.charNp.node().getCharacter()
        self.eyes = self.charNp.findAllMatches("**/+EyeballNode")
        self.lidUpperMorph = self.char.findSlider("CloseLidUpL+CloseLidUpR")
        self.lidLowerMorph = self.char.findSlider("CloseLidLoL+CloseLidLoR")
        self.lowerEyeLidCloseAmount = 0.0
        self.upperEyeLidCloseAmount = 0.0
        self.lowerBlinkAmount = 0.0
        self.upperBlinkAmount = 0.0
        self.currLook = None
        self.nextLookTime = 0.0
        self.lookIval = None
        self.eyelidsTask = None
        self.blinkTask = None
        self.lookAroundTask = None

        # Set up the animation channel to move the eyelid morphs.
        self.chan = AnimChannelUser("eyes-chan", self.char, True)
        self.chan.setFlags(AnimChannel.FDelta)
        index = self.char.addChannel(self.chan)
        # Play it on layer 7 above lip sync and all joint
        # animations.
        self.char.loop(index, True, 7)

        if debug:
            headSegs = LineSegs('head')
            headSegs.setColor((1, 0, 0, 1))
            headSegs.moveTo((0, 0, 0))
            headSegs.drawTo(Vec3.forward())
            self.headSegsNp = self.charNp.attachNewNode(headSegs.create())
            self.headSegsNp.setScale(16)
        else:
            self.headSegsNp = None

    def enable(self):
        self.disable()

        if not self.eyes:
            return

        self.eyelidsTask = base.taskMgr.add(self.__eyelids, 'eyelids')
        self.blinkTask = base.taskMgr.add(self.__blink, 'blink')
        self.lookAroundTask = base.taskMgr.add(self.__lookAround, 'lookAround')

    def disable(self):
        if self.lookIval:
            self.lookIval.finish()
            self.lookIval = None
        if self.eyelidsTask:
            self.eyelidsTask.remove()
            self.eyelidsTask = None
        if self.blinkTask:
            self.blinkTask.remove()
            self.blinkTask = None
        if self.lookAroundTask:
            self.lookAroundTask.remove()
            self.lookAroundTask = None

    def cleanup(self):
        self.disable()
        if self.headSegsNp:
            self.headSegsNp.removeNode()
            self.headSegsNp = None
        self.eyes = None
        self.char = None
        self.charNp = None

    def __eyelids(self, task):
        if self.lidUpperMorph < 0 or self.lidLowerMorph < 0:
            # No eyelid sliders.
            return task.done

        self.chan.setSlider(self.lidUpperMorph, min(0.8, self.upperEyeLidCloseAmount + self.upperBlinkAmount))
        self.chan.setSlider(self.lidLowerMorph, min(1.0 - self.chan.getSlider(self.lidUpperMorph), self.lowerEyeLidCloseAmount + self.lowerBlinkAmount))

        return task.cont

    def __doBlink(self):
        def moveUpEyeLid(val):
            self.upperBlinkAmount = val

        def moveLoEyeLid(val):
            self.lowerBlinkAmount = val

        p = Parallel()

        upIval = Sequence()
        upIval.append(LerpFunc(moveUpEyeLid, fromData=0, toData=0.8, duration=0.05))
        upIval.append(LerpFunc(moveUpEyeLid, fromData=0.8, toData=0, duration=0.1))

        loIval = Sequence()
        loIval.append(LerpFunc(moveLoEyeLid, fromData=0, toData=0.2, duration=0.05))
        loIval.append(LerpFunc(moveLoEyeLid, fromData=0.2, toData=0, duration=0.1))

        p.append(upIval)
        p.append(loIval)
        p.start()

    def __blink(self, task):
        self.__doBlink()

        r = random.random()
        if r < 0.1:
            t = 0.2
        else:
            t = r * 4.0 + 1.0
        task.delayTime = t
        return task.again

    def __lookAround(self, task):
        # Pick a new look point if the head rotates too far away from the current
        # look point.

        charWorld = self.charNp.getMat(base.render)

        headJoint = self.char.findJoint("bip_head")

        currHeadLocal = self.char.getJointValue(headJoint)
        pos = Vec3()
        hpr = Vec3()
        scale = Vec3()
        shear = Vec3()
        decomposeMatrix(currHeadLocal, scale, shear, hpr, pos)
        # Apply rotation offset fixup.
        hpr += self.headRotationOffset
        currHeadLocalFixed = Mat4()
        composeMatrix(currHeadLocalFixed, scale, shear, hpr, pos)

        headParent = self.char.getJointParent(headJoint)
        headParentChar = self.char.getJointNetTransform(headParent)

        currHeadCharFixed = currHeadLocalFixed * headParentChar
        currHeadChar = currHeadLocal * headParentChar

        currHeadRotChar = Quat()
        currHeadRotChar.setFromMatrix(currHeadCharFixed)

        numEyes = len(self.eyes)
        eyeMiddle = Point3(0)
        for eye in self.eyes:
            eyeMiddle += eye.node().getEyeOffset().getPos()
        eyeMiddle /= numEyes
        currEyePosChar = currHeadChar.xformPoint(eyeMiddle)

        if self.headSegsNp:
            self.headSegsNp.setPos(currEyePosChar)
            self.headSegsNp.setQuat(currHeadRotChar)

        snap = False

        if self.currLook is not None:
            eyeToLook = Vec3(self.currLook - currEyePosChar).normalized()

            q = Quat()
            lookAt(q, eyeToLook)
            eyeToLookHpr = q.getHpr()
            currHeadHpr = currHeadRotChar.getHpr()

            horizAngle = currHeadHpr[0] - eyeToLookHpr[0]
            vertAngle = currHeadHpr[1] - eyeToLookHpr[1]

            upperPerct = min(1.0, (vertAngle + 35) / 70)
            lowerPerct = 1 - upperPerct

            self.upperEyeLidCloseAmount = upperPerct * (0.45 * 0.8)
            self.lowerEyeLidCloseAmount = lowerPerct * (0.25 * 0.8)

            if abs(horizAngle) > 35 or abs(vertAngle) > 25:
                # Head rotated too far away from look point, pick a new one now.
                self.nextLookTime = 0.0
                snap = True

        now = base.clockMgr.getTime()

        if now >= self.nextLookTime:
            # It's time to look somewhere else.

            lookYaw = random.uniform(-20, 20)
            lookPitch = random.uniform(-20, 20)

            q = Quat()
            q.setHpr((lookYaw, lookPitch, 0))

            lookPoint = currEyePosChar + currHeadRotChar.xform(q.getForward()) * 128

            def lookLerp(frac, origin, delta):
                for eyeNp in self.eyes:
                    eyeNp.node().setViewTarget(self.charNp, origin + delta * frac)

            if self.currLook is not None and not snap:
                # Lerp to look point.
                if self.lookIval:
                    self.lookIval.finish()
                self.lookIval = LerpFunc(lookLerp, fromData=0, toData=1, duration=0.075, extraArgs=[Point3(self.currLook), lookPoint - self.currLook])
                self.lookIval.start()
            else:
                if self.lookIval:
                    self.lookIval.finish()
                    self.lookIval = None
                for eyeNp in self.eyes:
                    eyeNp.node().setViewTarget(self.charNp, lookPoint)

            self.currLook = Point3(lookPoint)
            self.nextLookTime = now + (random.random() * 6.0 + 1.0)

        return task.cont

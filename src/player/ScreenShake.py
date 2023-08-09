"""ScreenShake module: contains the ScreenShake class."""

import math
import random

from panda3d.core import *

SHAKE_START = 0
SHAKE_STOP = 1
SHAKE_AMPLITUDE = 2
SHAKE_FREQUENCY = 3
MAX_SHAKES = 32

class Shake:
    pass

class ScreenShake:

    def __init__(self):
        self.shakes = []
        self.shakeAppliedAngle = 0
        self.shakeAppliedOffset = Vec3(0)

    def clearAllShakes(self):
        self.shakes = []

    def addShake(self, command, localAmplitude, freq, duration):
        if command == SHAKE_START and len(self.shakes) < MAX_SHAKES:
            shakeData = Shake()
            shakeData.amplitude = localAmplitude
            shakeData.frequency = freq
            shakeData.duration = duration
            shakeData.nextShake = 0
            shakeData.endTime = base.clockMgr.getTime() + duration
            shakeData.command = command
            shakeData.offset = Vec3(0)
            shakeData.angle = 0
            self.shakes.append(shakeData)
        elif command == SHAKE_STOP:
            self.clearAllShakes()
        #elif command == SHAKE_AMPLITUDE:

    def calcShake(self):
        self.shakeAppliedOffset = Vec3(0)
        self.shakeAppliedAngle = 0

        for shake in list(self.shakes):

            if (base.clockMgr.getTime() > shake.endTime) or shake.duration <= 0 or shake.amplitude <= 0 or shake.frequency <= 0:
                # Retire this shake.
                self.shakes.remove(shake)
                continue

            if base.clockMgr.getTime() > shake.nextShake:
                # Higher frequency means we recalc the extents more often and pertur the display again.
                shake.nextShake = base.clockMgr.getTime() + (1.0 / shake.frequency)

                # Compute random shake extents (the shake will settle down from this).
                for i in range(3):
                    shake.offset[i] = random.uniform(-shake.amplitude, shake.amplitude)
                shake.angle = random.uniform(-shake.amplitude*0.25, shake.amplitude*0.25)

            # Ramp down amplitude over duration (fraction goes from 1 to 0 linearly with slope 1/duration)
            fraction = (shake.endTime - base.clockMgr.getTime()) / shake.duration

            # Ramp up frequency over duration
            if fraction:
                freq = shake.frequency / fraction
            else:
                freq = 0

            # Square fraction to approach zero more quickly.
            fraction *= fraction

            # Sine wave that slowly settings to zero
            angle = base.clockMgr.getTime() * freq
            if angle > 1e8:
                angle = 1e8
            fraction *= math.sin(angle)

            # Add to view origin
            self.shakeAppliedOffset += shake.offset * fraction
            self.shakeAppliedAngle += shake.angle * fraction

            # Drop amplitude a bit, less for higher frequency shakes.
            shake.amplitude -= shake.amplitude * (base.clockMgr.getDeltaTime() / (shake.duration * shake.frequency))

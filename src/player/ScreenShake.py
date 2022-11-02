"""ScreenShake module: contains the ScreenShake class."""

from panda3d.core import *

import random
import math

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
            shakeData.endTime = globalClock.frame_time + duration
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

            if (globalClock.frame_time > shake.endTime) or shake.duration <= 0 or shake.amplitude <= 0 or shake.frequency <= 0:
                # Retire this shake.
                self.shakes.remove(shake)
                continue

            if globalClock.frame_time > shake.nextShake:
                # Higher frequency means we recalc the extents more often and pertur the display again.
                shake.nextShake = globalClock.frame_time + (1.0 / shake.frequency)

                # Compute random shake extents (the shake will settle down from this).
                for i in range(3):
                    shake.offset[i] = random.uniform(-shake.amplitude, shake.amplitude)
                shake.angle = random.uniform(-shake.amplitude*0.25, shake.amplitude*0.25)

            # Ramp down amplitude over duration (fraction goes from 1 to 0 linearly with slope 1/duration)
            fraction = (shake.endTime - globalClock.frame_time) / shake.duration

            # Ramp up frequency over duration
            if fraction:
                freq = shake.frequency / fraction
            else:
                freq = 0

            # Square fraction to approach zero more quickly.
            fraction *= fraction

            # Sine wave that slowly settings to zero
            angle = globalClock.frame_time * freq
            if angle > 1e8:
                angle = 1e8
            fraction *= math.sin(angle)

            # Add to view origin
            self.shakeAppliedOffset += shake.offset * fraction
            self.shakeAppliedAngle += shake.angle * fraction

            # Drop amplitude a bit, less for higher frequency shakes.
            shake.amplitude -= shake.amplitude * (globalClock.dt / (shake.duration * shake.frequency))

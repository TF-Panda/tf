"""Expressions module: contains the Expressions class."""

import math

from tf.tfbase import TFGlobals

from panda3d.core import *

#class ExpressionDef:

#    def __init__(self, )

class Expression:

    def __init__(self, name, startTime, maxWeight, duration = -1, oscillation = 0.0, oscillationSpeed = 0.0):
        self.name = name
        self.startTime = startTime
        self.maxWeight = maxWeight
        self.duration = duration
        self.oscillation = oscillation
        self.oscillationSpeed = oscillationSpeed

        self.weight = 0.0
        self.oscillationWeight = 0.0
        self.expired = False

class Expressions:
    """
    This class manages facial expressions for a character with facial
    expression morph targets.

    It manages fading in and out of different facial expressions and cross
    fading betwween facial expression changes.
    """

    def __init__(self, character, expressionDefs):
        # Character to move sliders on.
        self.character = character
        # Defines the morph targets associated with different expressions.
        self.expressions = expressionDefs

        # List of active facial expressions.
        # They are layered on top of each other.
        self.expressionList = []

        # Create animation channel to move facial expression morphs.
        self.chan = AnimChannelUser("expressions-chan", self.character, True)
        self.chan.setFlags(AnimChannel.FDelta)
        index = self.character.addChannel(self.chan)
        # Layer 8 is above all joint animations, lip sync, and eyelids.
        self.character.loop(index, True, 8)

    def hasExpression(self, name):
        for exp in self.expressionList:
            if exp.name == name:
                return True
        return False

    def cleanup(self):
        self.expressionList = None
        self.expressions = None
        self.character = None

    def clearExpression(self, name):
        self.expressionList = [exp for exp in self.expressionList if exp.name != name]

    def resetExpressions(self):
        """
        Sets all sliders used by each expression to zero.
        """
        for sliderNameList in self.expressions.values():
            for sliderName in sliderNameList:
                slider = self.character.findSlider(sliderName)
                if slider >= 0:
                    self.chan.setSlider(slider, 0.0)
        self.expressionList = []

    def clearNonBaseExpressions(self):
        if len(self.expressionList) == 0:
            return
        self.expressionList = [self.expressionList[0]]

    def pushExpression(self, name, maxWeight, duration = -1, oscillation = 0.0, oscillationSpeed = 0.0):
        self.expressionList.append(Expression(name, globalClock.frame_time, maxWeight, duration, oscillation, oscillationSpeed))

    def updateExpression(self, exp):
        now = globalClock.frame_time
        elapsed = now - exp.startTime

        if exp.duration > 0 and elapsed >= exp.duration:
            exp.weight = 0.0
            exp.expired = True
            return

        if elapsed < 0.5:
            # Fading in.
            exp.weight = TFGlobals.simpleSpline((elapsed / 0.5) * exp.maxWeight)

        elif exp.duration > 0 and ((exp.duration - elapsed) < 0.5):
            # Fading out.
            exp.weight = max(0.0, TFGlobals.simpleSpline(((exp.duration - elapsed) / 0.5) * exp.maxWeight))

        else:
            # Full weight.
            exp.weight = exp.maxWeight

            # Apply oscillation?
            if exp.oscillation > 0.0:
                fullWeightElapsed = elapsed - 0.5
                exp.oscillationWeight = (1 - (math.cos(fullWeightElapsed * exp.oscillationSpeed) * 0.5 + 0.5)) * exp.oscillation

    def update(self):
        for exp in self.expressionList:
            self.updateExpression(exp)

        # Filter down to just the still active ones.
        self.expressionList[:] = [exp for exp in self.expressionList if not exp.expired]

        # Now layer them.
        remainder = 1.0

        weights = []
        for exp in reversed(self.expressionList):
            if remainder <= 0.0:
                weights.append(0.0)
                continue

            weight = min(remainder, max(0.0, exp.weight - exp.oscillationWeight))
            weights.append(weight)

            remainder -= weight

        for i in range(len(weights)):
            exp = self.expressionList[len(weights) - i - 1]
            for sliderName in self.expressions[exp.name]:
                slider = self.character.findSlider(sliderName)
                if slider >= 0:
                    self.chan.setSlider(slider, weights[i])

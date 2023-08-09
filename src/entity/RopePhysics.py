"""RopePhysics module: contains the RopePhysics class."""

import math
import random

from panda3d.core import Point3, Vec3


class RopePhysicsNode:

    def __init__(self, pos):
        self.origPos = Point3(pos)
        self.pos = pos
        self.prevPos = pos
        self.smoothPos = pos
        self.fixed = False

class RopePhysicsConstraint:

    def __init__(self, nodeA, nodeB):
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.springDist = 0.0

class RopePhysicsSimulation:

    def __init__(self):
        self.nodes = []
        self.springs = []
        self.predictedTime = 0.0
        self.timeStep = 1 / 50.0
        self.tick = 0
        #self.springDist = 0.0
        self.currentGustTimer = 0
        self.currentGustLifetime = 0
        self.timeToNextGust = 0
        self.windDir = Vec3.forward()
        self.windAccel = Vec3()

    def randomVector(self, low, hi):
        v = Vec3(
            random.uniform(low, hi),
            random.uniform(low, hi),
            random.uniform(low, hi)
        )
        return v

    def updateWind(self, dt):
        if self.currentGustTimer < self.currentGustLifetime:
            div = self.currentGustTimer / self.currentGustLifetime
            scale = 1 - math.cos(div * math.pi)
            self.windAccel = self.windDir * scale
        else:
            self.windAccel = Vec3()

        self.currentGustTimer += dt
        self.timeToNextGust -= dt
        if self.timeToNextGust <= 0:
            self.windDir = self.randomVector(-1, 1).normalized()

            self.windDir *= 50
            self.windDir *= random.uniform(-1, 1)

            self.currentGustTimer = 0
            self.currentGustLifetime = random.uniform(2, 3)
            self.timeToNextGust = random.uniform(3, 4)

    def getTime(self):
        return self.timeStep * self.tick

    def getNodeForces(self, node):
        if node.fixed:
            return Vec3(0)
        accel = Vec3(0, 0, -1500)
        accel += self.windAccel

        return accel

    def constraintIter(self):
        for spring in self.springs:
            to = spring.nodeA.pos - spring.nodeB.pos

            dist = to.length()

            if dist > spring.springDist:
                #allGood = False
                to *= 1 - (spring.springDist / dist)
                if spring.nodeA.fixed:
                    spring.nodeB.pos += to
                elif spring.nodeB.fixed:
                    spring.nodeA.pos -= to
                else:
                    spring.nodeA.pos -= to * 0.5
                    spring.nodeB.pos += to * 0.5

    def applyConstraints(self):
        for i in range(3):
            self.constraintIter()
        #self.constraintIter()

    def simulate(self, dt, damping):
        self.updateWind(dt)

        self.predictedTime += dt
        newTick = int(math.ceil(self.predictedTime / self.timeStep))
        numTicks = newTick - self.tick

        timeStepMul = self.timeStep * self.timeStep * 0.5

        for i in range(numTicks):
            for node in self.nodes:

                accel = self.getNodeForces(node)

                prevPos = node.pos
                node.pos = node.pos + (node.pos - node.prevPos) * damping + accel * timeStepMul
                node.prevPos = prevPos

            self.applyConstraints()

        self.tick = newTick

        interpolant = (self.predictedTime - (self.getTime() - self.timeStep)) / self.timeStep
        for node in self.nodes:
            node.smoothPos = node.prevPos + (node.pos - node.prevPos) * interpolant

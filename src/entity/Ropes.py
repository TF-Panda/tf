"""Ropes module: contains the Ropes class."""

from panda3d.core import *
from panda3d.pphysics import *
from panda3d.tf import RopePhysicsSimulation, QuickRopeNode

from .DistributedEntity import DistributedEntity


class RopeKeyFrame(DistributedEntity):

    def __init__(self):
        DistributedEntity.__init__(self)
        # DoId of the next keyframe.
        # If we have one, we will generate a rope (nurbs curve)
        # between this node and the next one.
        self.nextKeyFrame = -1
        self.slack = 0
        self.subdiv = 1
        self.thickness = 1
        self.curve = None
        self.ropeNode = None
        self.sim = None

    def startRope(self):
        base.ropeMgr.addRope(self.sim)

    def stopRope(self):
        if self.sim:
            base.ropeMgr.removeRope(self.sim)

    def destroyRope(self):
        self.stopRope()
        self.sim = None
        self.curve = None
        if self.ropeNode:
            self.ropeNode.removeNode()
            self.ropeNode = None

    def genCurve(self):
        self.destroyRope()

        start = self.getPos()
        endNode = base.cr.doId2do.get(self.nextKeyFrame)
        if not endNode:
            return
        end = endNode.getPos()
        delta = end - start
        numVerts = 10
        if numVerts < 3:
            return
        thick = self.thickness
        slack = self.slack
        if base.sky3DRoot.isAncestorOf(self):
            thick /= 16
            slack /= 16

        springDist = (delta.length() + slack - 100) / (numVerts - 1)

        self.sim = RopePhysicsSimulation()

        for i in range(numVerts):
            frac = float(i) / (numVerts - 1)
            pos = start + delta * frac
            fixed = (i == 0 or i == (numVerts - 1))
            self.sim.addNode(pos, fixed)

        self.sim.genSprings(springDist)

        rope = QuickRopeNode("rope", numVerts, thick, self.subdiv)
        self.sim.setQuickRope(rope)
        self.ropeNode = NodePath(rope)
        self.ropeNode.wrtReparentTo(self)
        self.ropeNode.setColorScale((0, 0, 0, 1))

        self.startRope()

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        self.genCurve()

    def disable(self):
        self.destroyRope()
        DistributedEntity.disable(self)

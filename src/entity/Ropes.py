"""Ropes module: contains the Ropes class."""

from panda3d.core import *
from panda3d.pphysics import *

from .DistributedEntity import DistributedEntity

from . import RopePhysics

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

    def updateCurve(self, task):
        self.sim.simulate(globalClock.dt, 0.98)
        for i in range(len(self.sim.nodes)):
            self.curve.setVertex(i, self.sim.nodes[i].smoothPos)
        return task.cont

    def startRope(self):
        self.addTask(self.updateCurve, "updateCurve", sim=False, appendTask=True)

    def stopRope(self):
        self.removeTask("updateCurve")

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
        thick = self.thickness * 2
        slack = self.slack
        if base.sky3DRoot.isAncestorOf(self):
            thick /= 16
            slack /= 16

        springDist = (delta.length() + slack - 100) / (numVerts - 1)

        self.sim = RopePhysics.RopePhysicsSimulation()

        for i in range(numVerts):
            frac = float(i) / (numVerts - 1)
            pos = start + delta * frac
            node = RopePhysics.RopePhysicsNode(pos)
            if i == 0 or i == (numVerts - 1):
                node.fixed = True
            self.sim.nodes.append(node)

        for i in range(1, len(self.sim.nodes)):
            nodeA = self.sim.nodes[i - 1]
            nodeB = self.sim.nodes[i]
            spring = RopePhysics.RopePhysicsConstraint(nodeA, nodeB)
            spring.springDist = springDist
            self.sim.springs.append(spring)

        self.curve = NurbsCurveEvaluator()
        self.curve.setOrder(4)
        self.curve.reset(numVerts)

        rope = RopeNode("rope")
        rope.setCurve(self.curve)
        rope.setThickness(thick)
        rope.setNumSubdiv(self.subdiv)
        #rope.setNumSlices(1)
        rope.setRenderMode(RopeNode.RMBillboard)
        rope.setNormalMode(RopeNode.NMNone)
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

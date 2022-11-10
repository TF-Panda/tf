"""Ropes module: contains the Ropes class."""

from panda3d.core import *

from .DistributedEntity import DistributedEntity

from direct.showutil.Rope import Rope

import math

class RopeKeyFrame(DistributedEntity):

    def __init__(self):
        DistributedEntity.__init__(self)
        # DoId of the next keyframe.
        # If we have one, we will generate a rope (nurbs curve)
        # between this node and the next one.
        self.nextKeyFrame = -1
        self.nextKeyFrameTargetName = ""
        self.slack = 0
        self.subdiv = 1
        self.thickness = 1
        self.rope = None

    if IS_CLIENT:
        def genCurve(self):
            if self.rope:
                self.rope.removeNode()
                self.rope = None

            start = self.getPos()
            endNode = base.cr.doId2do.get(self.nextKeyFrame)
            if not endNode:
                return
            end = endNode.getPos()

            self.rope = Rope()
            self.rope.setColorScale(0, 0, 0, 1)
            self.rope.ropeNode.setRenderMode(RopeNode.RMBillboard)
            self.rope.ropeNode.setUseVertexColor(0)
            self.rope.ropeNode.setUseVertexThickness(1)
            thick = self.thickness * 2
            slack = self.slack * 0.5
            if base.sky3DRoot.isAncestorOf(self):
                thick /= 16
                slack /= 16
            ps = []
            totalPoints = 2 + self.subdiv
            for i in range(totalPoints):
                t = i / (totalPoints - 1)
                point = start + (end - start) * t
                point += Vec3.down() * math.sin(t * math.pi) * slack
                ps.append({'node': base.render, 'point': point, 'thickness': thick})
            self.rope.setup(4, ps)
            #self.rope.reparentTo(self.getParent())

        def announceGenerate(self):
            DistributedEntity.announceGenerate(self)
            self.genCurve()

        def disable(self):
            if self.rope:
                self.rope.removeNode()
                self.rope = None
            DistributedEntity.disable(self)

    else:
        def initFromLevel(self, ent, props):
            DistributedEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("width"):
                self.thickness = props.getAttributeValue("width").getFloat()
            if props.hasAttribute("Subdiv"):
                self.subdiv = props.getAttributeValue("Subdiv").getInt()
            if props.hasAttribute("Slack"):
                self.slack = props.getAttributeValue("Slack").getFloat()
            if props.hasAttribute("NextKey"):
                self.nextKeyFrameTargetName = props.getAttributeValue("NextKey").getString()

        def announceGenerate(self):
            DistributedEntity.announceGenerate(self)
            if self.nextKeyFrameTargetName:
                ent = base.entMgr.findExactEntity(self.nextKeyFrameTargetName)
                if ent:
                    self.nextKeyFrame = ent.doId

if not IS_CLIENT:
    RopeKeyFrameAI = RopeKeyFrame
    RopeKeyFrameAI.__name__ = 'RopeKeyFrameAI'

"""RopesAI module: contains the RopesAI class."""

from .DistributedEntity import DistributedEntityAI

class RopeKeyFrameAI(DistributedEntityAI):

    def __init__(self):
        DistributedEntityAI.__init__(self)
        # DoId of the next keyframe.
        # If we have one, we will generate a rope (nurbs curve)
        # between this node and the next one.
        self.nextKeyFrame = -1
        self.nextKeyFrameTargetName = ""
        self.slack = 0
        self.subdiv = 1
        self.thickness = 1

    def initFromLevel(self, ent, props):
        DistributedEntityAI.initFromLevel(self, ent, props)
        if props.hasAttribute("width"):
            self.thickness = props.getAttributeValue("width").getFloat()
        if props.hasAttribute("Subdiv"):
            self.subdiv = props.getAttributeValue("Subdiv").getInt()
        if props.hasAttribute("Slack"):
            self.slack = props.getAttributeValue("Slack").getFloat()
        if props.hasAttribute("NextKey"):
            self.nextKeyFrameTargetName = props.getAttributeValue("NextKey").getString()

    def announceGenerate(self):
        DistributedEntityAI.announceGenerate(self)
        if self.nextKeyFrameTargetName:
            ent = base.entMgr.findExactEntity(self.nextKeyFrameTargetName)
            if ent:
                self.nextKeyFrame = ent.doId

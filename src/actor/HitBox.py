
class HitBoxGroup:

    Generic = 0
    Head = 1
    Chest = 2
    Stomach = 3
    LeftArm = 4
    RightArm = 5
    LeftLeg = 6
    RightLeg = 7
    Neck = 8

class HitBox:

    def __init__(self, group, body, joint):
        self.group = group
        self.body = body
        self.joint = joint

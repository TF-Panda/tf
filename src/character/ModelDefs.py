
from panda3d.core import *

import math

from .Activity import Activity
from .HitBox import HitBoxGroup
from .AnimEvents import AnimEvent, AnimEventType

#from test_talker.EngineerRagdoll import EngineerRagdoll
#from test_talker.SoldierRagdoll import SoldierRagdoll
#from test_talker.DemoRagdoll import DemoRagdoll

class EngineerModel:
    @staticmethod
    def createRagdoll(char):
        #return EngineerRagdoll(char.modelNp)
        return None

    @staticmethod
    def createHitBoxes(char):
        # group, jointname, (minx, miny, minz), (maxx, maxy, maxz)
        char.addHitBox(1, "bip_head",       (-6, -11, -8),      (6, 4, 6))
        char.addHitBox(0, "bip_pelvis",     (-9, -0.5, -7.5),   (9, 11.5, 3.5))
        char.addHitBox(3, "bip_spine_0",    (-9, -2, -10),      (9, 4, 4))
        char.addHitBox(3, "bip_spine_1",    (-9, -3, -10.5),    (9, 3, 4.5))
        char.addHitBox(2, "bip_spine_2",    (-10, -3, -9),      (10, 3, 5))
        char.addHitBox(2, "bip_spine_3",    (-10, -3.5, -10),   (10, 1.5, 4))
        char.addHitBox(4, "bip_upperArm_L", (0, -3.5, -2.75),   (12, 3.5, 3.25))
        char.addHitBox(4, "bip_lowerArm_L", (0, -2.25, -3.25),  (13, 2.25, 3.25))
        char.addHitBox(4, "bip_hand_L",     (-3.5, -10, -3),    (1.5, 0, 5))
        char.addHitBox(5, "bip_upperArm_R", (0, -3.5, -2.75),   (12, 3.5, 3.25))
        char.addHitBox(5, "bip_lowerArm_R", (0, -3.25, -2.75),  (13, 3.25, 2.75))
        char.addHitBox(5, "bip_hand_R",     (-2.5, 0.5, -3.5),  (2.5, 9.5, 4.5))
        char.addHitBox(6, "bip_hip_L",      (2, -4, -5),        (16, 4, 4))
        char.addHitBox(6, "bip_knee_L",     (0, -2.25, -4.5),   (16, 3.25, 2.5))
        char.addHitBox(6, "bip_foot_L",     (-2, -10, -3),      (2, 2, 3))
        char.addHitBox(7, "bip_hip_R",      (2, -4, -5),        (16, 4, 4))
        char.addHitBox(7, "bip_knee_R",     (0, -3.25, -4.5),   (16, 2.25, 2.5))
        char.addHitBox(7, "bip_foot_R",     (-2, -2, -2.5),     (2, 10, 3.5))

class SoldierModel:
    @staticmethod
    def createRagdoll(char):
        #return SoldierRagdoll(char.modelNp)
        return None

    @staticmethod
    def createHitBoxes(char):
        char.addHitBox(1, "bip_head", (-6.25, -9, -7.55), (6.25, 5, 5.45))
        char.addHitBox(0, "bip_pelvis", (-10.5, -3, -9), (10.5, 11, 7))
        char.addHitBox(3, "bip_spine_0", (-9.5, -1.5, -10), (9.5, 5.5, 5))
        char.addHitBox(3, "bip_spine_1", (-10, -2, -10.5), (10, 4, 3.5))
        char.addHitBox(2, "bip_spine_2", (-10, -4, -11), (10, 4, 5))
        char.addHitBox(2, "bip_spine_3", (-10, -4.5, -7), (10, 1.5, 5))
        char.addHitBox(4, "bip_upperArm_L", (0, -4, -3), (14, 4, 3))
        char.addHitBox(4, "bip_lowerArm_L", (0, -2.75, -4), (14, 3.75, 4))
        char.addHitBox(4, "bip_hand_L", (-2.75, -10, -2.5), (1.75, 0, 4.5))
        char.addHitBox(5, "bip_upperArm_R", (0, -4, -3), (14, 4, 3))
        char.addHitBox(5, "bip_lowerArm_R", (0, -4, -3.75), (14, 4, 2.75))
        char.addHitBox(5, "bip_hand_R", (-1.75, 0, -4.5), (2.75, 10, 2.5))
        char.addHitBox(6, "bip_hip_L", (1.5, -5.5, -4), (16.5, 4.5, 4))
        char.addHitBox(6, "bip_knee_L", (0, -2, -5), (18, 4, 2))
        char.addHitBox(6, "bip_foot_L", (-2.5, -11, -3.75), (2.5, 3, 2.25))
        char.addHitBox(7, "bip_hip_R", (1.5, -4.5, -4), (16.5, 5.5, 4))
        char.addHitBox(7, "bip_knee_R", (0, -4, -5), (18, 2, 2))
        char.addHitBox(7, "bip_foot_R", (-2.5, -3, -2.25), (2.5, 11, 3.75))

class DemoModel:

    @staticmethod
    def createRagdoll(char):
        #return DemoRagdoll(char.modelNp)
        return None

    @staticmethod
    def createHitBoxes(char):
        char.addHitBox(1, "bip_head", (-6, -8, -7.5), (6, 5, 4.5))
        char.addHitBox(0, "bip_pelvis", (-9, 0, -5.5), (9, 10, 5.5))
        char.addHitBox(3, "bip_spine_0", (-10, -2, -10), (10, 4, 6))
        char.addHitBox(3, "bip_spine_1", (-11, -3, -11), (11, 3, 5))
        char.addHitBox(2, "bip_spine_2", (-11.5, -3, -11), (11.5, 3, 5))
        char.addHitBox(2, "bip_spine_3", (-13.11, -4, -10), (13.11, 2, 5))
        char.addHitBox(4, "bip_upperArm_L", (0, -3, -4.75), (16, 3, 2.75))
        char.addHitBox(4, "bip_lowerArm_L", (0, -2.25, -4.25), (13, 2.25, 2.75))
        char.addHitBox(4, "bip_hand_L", (-5, -10, -3), (1, 0, 5))
        char.addHitBox(5, "bip_upperArm_R", (0, -2.75, -3), (16, 4.75, 3))
        char.addHitBox(5, "bip_lowerArm_R", (0, -2.25, -2.6), (13, 4.25, 2.1))
        char.addHitBox(5, "bip_hand_R", (-1, 0, -5), (5, 10, 3))
        char.addHitBox(6, "bip_hip_L", (1.5, -5, -5), (18.5, 3, 4))
        char.addHitBox(6, "bip_knee_L", (-0.5, -2.5, -4.5), (20.5, 3, 2.5))
        char.addHitBox(6, "bip_foot_L", (-2.45, -11.5, -4), (3.05, 3.5, 2))
        char.addHitBox(7, "bip_hip_R", (1.5, -4, -3), (18.5, 5, 5))
        char.addHitBox(7, "bip_knee_R", (-0.5, -3, -4.5), (20.5, 2.5, 2.5))
        char.addHitBox(7, "bip_foot_R", (-3.05, -3.5, -2), (2.45, 11.5, 4))

ModelDefs = {
  "tfmodels/src/char/engineer/engineer.pmdl": EngineerModel,
  "tfmodels/src/char/soldier/soldier.pmdl": SoldierModel,
  "tfmodels/src/char/demo/demo.pmdl": DemoModel
}

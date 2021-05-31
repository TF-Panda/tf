
"""
This file creates AnimSequences for a model filename.  This exists because I
haven't implemented a way to describe AnimSequences in the pmdl file.
"""

from panda3d.core import *

import math

from .Activity import Activity
from .HitBox import HitBoxGroup
from .AnimEvents import AnimEvent, AnimEventType

from test_talker.EngineerRagdoll import EngineerRagdoll

noBonesDesc = WeightListDesc("nobones")
noBonesDesc.setWeight("bip_pelvis", 0.0)

MeleeHipsTorso = WeightListDesc("Melee_HipsTorso")
MeleeHipsTorso.setWeight("bip_pelvis", 0.75)
MeleeHipsTorso.setWeight("bip_hip_R", 0.0)
MeleeHipsTorso.setWeight("bip_hip_L", 0.0)
MeleeHipsTorso.setWeight("bip_collar_L", 0.0)
MeleeHipsTorso.setWeight("bip_collar_R", 0.0)
MeleeHipsTorso.setWeight("bip_spine_0", 0.75)

meleeArmsBlend = WeightListDesc("Melee_ArmsBlend")
meleeArmsBlend.setWeight("bip_pelvis", 0.0)
meleeArmsBlend.setWeight("bip_hip_R", 0.0)
meleeArmsBlend.setWeight("bip_hip_L", 0.0)
meleeArmsBlend.setWeight("bip_spine_1", 0.5)
meleeArmsBlend.setWeight("bip_spine_2", 0.7)
meleeArmsBlend.setWeight("bip_spine_3", 0.9)
meleeArmsBlend.setWeight("bip_collar_L", 1.0)
meleeArmsBlend.setWeight("bip_upperArm_L", 1.0)
meleeArmsBlend.setWeight("bip_lowerArm_L", 1.0)
meleeArmsBlend.setWeight("bip_collar_R", 1.0)
meleeArmsBlend.setWeight("bip_upperArm_R", 1.0)
meleeArmsBlend.setWeight("bip_lowerArm_R", 1.0)
meleeArmsBlend.setWeight("bip_head", 0.0)
meleeArmsBlend.setWeight("bip_neck", 0.0)

hipsUpperBodyDesc = WeightListDesc("HipsUpperBody")
hipsUpperBodyDesc.setWeight("bip_pelvis", 1.0)
hipsUpperBodyDesc.setWeight("bip_hip_R", 0.0)
hipsUpperBodyDesc.setWeight("bip_hip_L", 0.0)

DiagonalFactor = math.sqrt(2.) / 2.

def createSequence(char, controlName, flags = 0, activity = 0, activityWeight = 1):
    if (flags & AnimSequence.FAllZeros) != 0:
        seq = AnimSequence("seq_" + controlName)
    else:
        seq = AnimSequence("seq_" + controlName, char.anims[controlName])
    seq.setFlags(flags)
    seq.setActivity(activity, activityWeight)
    return seq

def createRunBlend(char, name, activity = 0):
    animControls = char.anims
    blend = AnimBlendNode2D("run_blend_" + name)
    blend.setInputX(char.findPoseParameter("move_x"))
    blend.setInputY(char.findPoseParameter("move_y"))
    blend.addInput(animControls['a_runCenter_' + name], Point2(0, 0))
    blend.addInput(animControls['a_runN_' + name], Point2(0, 1))
    blend.addInput(animControls['a_runS_' + name], Point2(0, -1))
    blend.addInput(animControls['a_runNE_' + name], Point2(DiagonalFactor, DiagonalFactor))
    blend.addInput(animControls['a_runNW_' + name], Point2(-DiagonalFactor, DiagonalFactor))
    blend.addInput(animControls['a_runE_' + name], Point2(1, 0))
    blend.addInput(animControls['a_runW_' + name], Point2(-1, 0))
    blend.addInput(animControls['a_runSW_' + name], Point2(-DiagonalFactor, -DiagonalFactor))
    blend.addInput(animControls['a_runSE_' + name], Point2(DiagonalFactor, -DiagonalFactor))
    blendSeq = AnimSequence("run_blend_seq_" + name, blend)
    blendSeq.setFlags(AnimSequence.FZeroRootX | AnimSequence.FZeroRootY | AnimSequence.FLooping)
    blendSeq.setActivity(activity)
    return blendSeq

def createAimBlend(char, name, weights):
    animControls = char.anims
    blend = AnimBlendNode2D("aim_blend_" + name)
    blend.setInputX(char.findPoseParameter("look_yaw"))
    blend.setInputY(char.findPoseParameter("look_pitch"))
    blend.addInput(animControls['a_' + name + '_straight_up'], Point2(0, 1))
    blend.addInput(animControls['a_' + name + '_straight_up'], Point2(1, 1))
    blend.addInput(animControls['a_' + name + '_straight_up'], Point2(-1, 1))
    blend.addInput(animControls['a_' + name + '_up_right'], Point2(1, 0.5))
    blend.addInput(animControls['a_' + name + '_up_center'], Point2(0, 0.5))
    blend.addInput(animControls['a_' + name + '_up_left'], Point2(-1, 0.5))
    blend.addInput(animControls['a_' + name + '_mid_right'], Point2(1, 0))
    blend.addInput(animControls['a_' + name + '_mid_center'], Point2(0, 0))
    blend.addInput(animControls['a_' + name + '_mid_left'], Point2(-1, 0))
    blend.addInput(animControls['a_' + name + '_down_right'], Point2(1, -0.5))
    blend.addInput(animControls['a_' + name + '_down_center'], Point2(0, -0.5))
    blend.addInput(animControls['a_' + name + '_down_left'], Point2(-1, -0.5))
    blendSeq = AnimSequence("aim_blend_seq_" + name, blend)
    blendSeq.setFlags(AnimSequence.FDelta | AnimSequence.FPost)
    blendSeq.setWeightList(weights)
    return blendSeq

class EngineerModel:
    @staticmethod
    def createRagdoll(char):
        return EngineerRagdoll(char.modelNp)

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

    @staticmethod
    def createSequences(char):
        char.modelNp.setH(180)

        noBonesWeights = WeightList(char.character, noBonesDesc)
        meleeHipsTorsoWeights = WeightList(char.character, MeleeHipsTorso)
        meleeArmsBlendWeights = WeightList(char.character, meleeArmsBlend)
        hipsUpperBodyWeights = WeightList(char.character, hipsUpperBodyDesc)

        primaryIdleAimLayer = createAimBlend(char, "PRIMARY_aimmatrix_idle", hipsUpperBodyWeights)
        primaryIdleSeq = createSequence(char, "stand_PRIMARY", AnimSequence.FLooping, Activity.Primary_Stand)
        primaryIdleSeq.addLayer(primaryIdleAimLayer)
        char.addSequence(primaryIdleSeq)

        primaryRunAimLayer = createAimBlend(char, "PRIMARY_aimmatrix_run", hipsUpperBodyWeights)
        primaryRunSeq = createRunBlend(char, "PRIMARY", Activity.Primary_Run)
        primaryRunSeq.addLayer(primaryRunAimLayer)
        char.addSequence(primaryRunSeq)

        primaryReloadSeq = createSequence(char, "ReloadStand_PRIMARY",
            AnimSequence.FDelta | AnimSequence.FPost, Activity.Primary_Reload_Stand)
        char.addSequence(primaryReloadSeq)
        primaryReloadLoopASeq = createSequence(char, "a_primary_reload_loop",
            AnimSequence.FDelta | AnimSequence.FPost,
            Activity.Primary_Reload_Stand_Loop, 2)
        char.addSequence(primaryReloadLoopASeq)
        primaryReloadLoopBSeq = createSequence(char, "b_primary_reload_loop",
            AnimSequence.FDelta | AnimSequence.FPost,
            Activity.Primary_Reload_Stand_Loop)
        char.addSequence(primaryReloadLoopBSeq)
        primaryReloadEndSeq = createSequence(char, "primary_reload_end",
            AnimSequence.FDelta | AnimSequence.FPost, Activity.Primary_Reload_Stand_End)
        char.addSequence(primaryReloadEndSeq)

        primaryAttackStandSeq = createSequence(char, "AttackStand_PRIMARY",
          AnimSequence.FDelta | AnimSequence.FPost, Activity.Primary_Attack_Stand)
        char.addSequence(primaryAttackStandSeq)

        meleeIdleAimLayer = createAimBlend(char, "MELEE_aimmatrix_idle", hipsUpperBodyWeights)
        meleeIdleSeq = createSequence(char, "stand_MELEE", AnimSequence.FLooping, Activity.Melee_Stand)
        meleeIdleSeq.addLayer(meleeIdleAimLayer)
        char.addSequence(meleeIdleSeq)

        meleeRunAimLayer = createAimBlend(char, "MELEE_aimmatrix_run", hipsUpperBodyWeights)
        meleeRunSeq = createRunBlend(char, "MELEE", Activity.Melee_Run)
        meleeRunSeq.addLayer(meleeRunAimLayer)
        char.addSequence(meleeRunSeq)

        meleeSwingArmsLayer = AnimSequence("swing_melee_armslayer", char.anims['armslayer_melee_swing'])
        meleeSwingArmsLayer.setWeightList(meleeArmsBlendWeights)
        meleeSwingBodyLayer = AnimSequence("swing_melee_bodylayer", char.anims['bodylayer_Melee_Swing'])
        meleeSwingBodyLayer.setWeightList(meleeHipsTorsoWeights)
        meleeSwingBodyLayer.setFlags(AnimSequence.FDelta | AnimSequence.FPost)
        meleeSwingSeq = AnimSequence("swing_melee_seq", char.anims['Melee_Swing'])
        meleeSwingSeq.setWeightList(noBonesWeights)
        meleeSwingSeq.addLayer(meleeSwingBodyLayer, 0, 1, 20, 24, True)
        meleeSwingSeq.addLayer(meleeSwingArmsLayer, 0, 5, 20, 24, True)
        meleeSwingSeq.setActivity(Activity.Melee_Attack_Stand)
        char.addSequence(meleeSwingSeq)

        layerTaunt01Seq = createSequence(char, "layer_taunt01")
        taunt01Seq = createSequence(char, "taunt01", 0, Activity.Taunt)
        taunt01Seq.addLayer(layerTaunt01Seq, 0, 5, 102, 106, False, False)
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 10, "Taunt.Engineer01HandClap")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 59, "Taunt.Engineer01HandClap2")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 22, "Taunt.Engineer01FootStomp")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 29, "Taunt.Engineer01FootStomp")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 68, "Taunt.Engineer01FootStomp")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 37, "Taunt.Engineer01FootStompLight")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 42, "Taunt.Engineer01FootStompLight")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 47, "Taunt.Engineer01FootStompLight")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 56, "Taunt.Engineer01FootStomp")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 57, "Taunt.Engineer01FootStompLight")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 60, "Taunt.Engineer01FootStompLight")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 79, "Taunt.Engineer01FootStompLight")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 86, "Taunt.Engineer01FootStompLight")
        taunt01Seq.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 88, "Taunt.Engineer01FootStomp")
        char.addSequence(taunt01Seq)

        layerTaunt02Seq = createSequence(char, "layer_taunt02")
        taunt02Seq = createSequence(char, "taunt02", 0, Activity.Taunt)
        taunt02Seq.addLayer(layerTaunt02Seq, 0, 5, 85, 90, False, False)
        char.addSequence(taunt02Seq)

        layerTaunt03Seq = createSequence(char, "layer_taunt03")
        taunt03Seq = createSequence(char, "taunt03", 0, Activity.Taunt)
        taunt03Seq.addLayer(layerTaunt03Seq, 0, 5, 133, 138, False, False)
        char.addSequence(taunt03Seq)

    @staticmethod
    def createPoseParameters(char):
        char.addPoseParameter("look_pitch", -1, 1)
        char.addPoseParameter("look_yaw", -1, 1)
        char.addPoseParameter("move_x", -1, 1)
        char.addPoseParameter("move_y", -1, 1)

class EngineerArmsModel:
    @staticmethod
    def createSequences(char):
        char.modelNp.setH(180)
        char.modelNp.node().setBounds(OmniBoundingVolume())
        char.modelNp.node().setFinal(1)

        fjDraw = char.createSimpleSequence("fj_draw", Activity.Primary_VM_Draw, False)
        fjDraw.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 1, "Weapon_Shotgun.Draw")
        char.addSequence(fjDraw)

        char.addSequence(char.createSimpleSequence("fj_idle", Activity.Primary_VM_Idle, True))

        fjFire = char.createSimpleSequence("fj_fire", Activity.Primary_VM_Fire, False, True)
        fjFire.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 7, "Weapon_ShotgunEngineer.Cock_Back")
        fjFire.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 12, "Weapon_ShotgunEngineer.Cock_Forward")
        char.addSequence(fjFire)

        char.addSequence(char.createSimpleSequence("fj_reload_start", Activity.Primary_VM_Reload_Start, False))
        fjReloadLoop = char.createSimpleSequence("fj_reload_loop", Activity.Primary_VM_Reload, True)
        fjReloadLoop.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 10, "Weapon_Shotgun.Reload")
        char.addSequence(fjReloadLoop)
        fjReloadEnd = char.createSimpleSequence("fj_reload_end", Activity.Primary_VM_Reload_End, False)
        fjReloadEnd.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 12, "Weapon_ShotgunEngineer.Cock_Back")
        fjReloadEnd.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 17, "Weapon_ShotgunEngineer.Cock_Forward")
        char.addSequence(fjReloadEnd)

        spkDraw = char.createSimpleSequence("spk_draw", Activity.Melee_VM_Draw, False)
        spkDraw.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 3, "Weapon_Wrench.Draw")
        spkDraw.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 3, "Weapon_Wrench.Draw2")
        spkDraw.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 20, "Weapon_Wrench.HitHand")
        char.addSequence(spkDraw)

        spkIdle = char.createSimpleSequence("spk_idle_tap", Activity.Melee_VM_Idle, True)
        spkIdle.addEvent(AnimEventType.Client, AnimEvent.Client_Play_Sound, 21, "Weapon_Wrench.HitHand")
        char.addSequence(spkIdle)

        char.addSequence(char.createSimpleSequence("spk_swing_a", Activity.Melee_VM_Swing, False))

class StaticModel:
    @staticmethod
    def createSequences(char):
        char.addSequence(char.createSimpleSequence("idle", 0, True))

ModelDefs = {
  "tfmodels/src/char/engineer/engineer.pmdl": EngineerModel,
  "tfmodels/src/char/engineer/engineer_viewmodel/c_engineer_arms.pmdl": EngineerArmsModel,
  "tfmodels/src/weapons/shotgun/c_shotgun.pmdl": StaticModel,
  "tfmodels/src/weapons/shotgun/w_shotgun.pmdl": StaticModel,
  "tfmodels/src/weapons/wrench/c_wrench.pmdl": StaticModel
}

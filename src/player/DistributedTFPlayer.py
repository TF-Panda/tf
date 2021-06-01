
from tf.character.DistributedChar import DistributedChar
from direct.distributed2.DistributedObject import DistributedObject
from .DistributedTFPlayerShared import DistributedTFPlayerShared

from .TFClass import *
from .TFPlayerAnimState import TFPlayerAnimState

from test_talker import Talker

from panda3d.core import *
from panda3d.direct import *

from direct.interval.IntervalGlobal import *

import random

sentences = Talker.parseSentences("scripts/game_sounds_vo_phonemes.txt")

phonemes = {}
phonemes['engineer'] = Talker.Phonemes("expressions/player/engineer/phonemes/phonemes.txt",
                               "expressions/player/engineer/phonemes/phonemes_weak.txt",
                               "expressions/player/engineer/phonemes/phonemes_strong.txt")

class DistributedTFPlayer(DistributedChar, DistributedTFPlayerShared):

    def __init__(self):
        DistributedChar.__init__(self)
        DistributedTFPlayerShared.__init__(self)

        self.animState = TFPlayerAnimState(self)

        self.lastActiveWeapon = -1

        self.lastPainTime = 0.0

        self.lastAngryTime = 0.0

        self.lastSwingTime = 0.0

        self.lastBapTime = 0.0

        self.talker = None

        self.classInfo = None

        self.ivLookPitch = InterpolatedFloat()
        #self.ivLookPitch.setLooping(True)
        self.addInterpolatedVar(self.ivLookPitch, self.getLookPitch, self.setLookPitch, DistributedObject.AnimationVar)

        self.ivLookYaw = InterpolatedFloat()
        #self.ivLookYaw.setLooping(True)
        self.addInterpolatedVar(self.ivLookYaw, self.getLookYaw, self.setLookYaw, DistributedObject.AnimationVar)

        self.ivMoveX = InterpolatedFloat()
        self.addInterpolatedVar(self.ivMoveX, self.getMoveX, self.setMoveX, DistributedObject.AnimationVar)

        self.ivMoveY = InterpolatedFloat()
        self.addInterpolatedVar(self.ivMoveY, self.getMoveY, self.setMoveY, DistributedObject.AnimationVar)

    def respawn(self):
        self.modelNp.show()

    def becomeRagdoll(self, *args, **kwargs):
        self.lastPainTime = 0.0
        return DistributedChar.becomeRagdoll(self, *args, **kwargs)

    def RecvProxy_activeWeapon(self, index):
        self.setActiveWeapon(index)

    def setActiveWeapon(self, index):
        if self.activeWeapon >= 0 and self.activeWeapon < len(self.weapons):
            # Deactive the old weapon.
            wpnId = self.weapons[self.activeWeapon]
            wpn = base.cr.doId2do.get(wpnId)
            if wpn:
                wpn.deactivate()

        self.activeWeapon = index
        if self.activeWeapon < 0 or self.activeWeapon >= len(self.weapons):
            return

        # Activate the new weapon.
        wpnId = self.weapons[self.activeWeapon]
        wpn = base.cr.doId2do.get(wpnId)
        if wpn:
            wpn.activate()

    def getVelocity(self):
        """
        Returns the world-space linear velocity of the player.
        """

        ctx = InterpolationContext()
        ctx.enableExtrapolation(True)
        ctx.setLastTimestamp(base.cr.lastServerTickTime)
        vel = Vec3()
        self.ivPos.getDerivativeSmoothVelocity(vel, globalClock.getFrameTime())
        q = self.getQuat(NodePath())
        q.invertInPlace()
        vel = q.xform(vel)
        return vel

    def setLookPitch(self, pitch):
        self.lookPitch = pitch
        self.getPoseParameter("look_pitch").setValue(pitch)

    def getLookPitch(self):
        return self.lookPitch

    def setLookYaw(self, yaw):
        self.lookYaw = yaw
        self.getPoseParameter("look_yaw").setValue(yaw)

    def getLookYaw(self):
        return self.lookYaw

    def setMoveX(self, moveX):
        self.moveX = moveX
        self.getPoseParameter("move_x").setValue(moveX)

    def getMoveX(self):
        return self.moveX

    def setMoveY(self, moveY):
        self.moveY = moveY
        self.getPoseParameter("move_y").setValue(moveY)

    def getMoveY(self):
        return self.moveY

    def postDataUpdate(self):
        DistributedChar.postDataUpdate(self)
        self.classInfo = ClassInfos[self.tfClass]

        if self.activeWeapon != self.lastActiveWeapon:
            self.lastActiveWeapon = self.activeWeapon

        #print(self.position, self.lookPitch, self.lookYaw)

    #def update(self):
    #    DistributedObject.update(self)

        #ctx = InterpolationContext()
        #ctx.enableExtrapolation(True)

        #self.prevPos = Point3(self.position)

    def speak(self):
        if self.talker.currSentence:
            return
        self.talker.speak(Filename("vo/engineer_cloakedspyidentify08.mp3"))

    def pain(self):
        now = globalClock.getFrameTime()
        if now - self.lastPainTime < 1.0:
            return

        painFilenames = [
            Filename("vo/engineer_painsevere01.mp3"),
            Filename("vo/engineer_painsevere02.mp3"),
            Filename("vo/engineer_painsevere03.mp3"),
            Filename("vo/engineer_painsevere04.mp3"),
            Filename("vo/engineer_painsevere05.mp3"),
            Filename("vo/engineer_painsevere06.mp3"),
            Filename("vo/engineer_painsevere07.mp3")
        ]

        self.talker.speak(random.choice(painFilenames))
        self.lastPainTime = now

    def swing(self):
        bamFilenames = [
            Filename("vo/engineer_gunslingerpunch01.mp3"),
            Filename("vo/engineer_gunslingerpunch02.mp3"),
            Filename("vo/engineer_gunslingerpunch03.mp3")
        ]

        now = globalClock.getFrameTime()
        if now - self.lastSwingTime < 1.0:
            return

        self.lastSwingTime = now

        if now - self.lastBapTime >= 5.0:
            self.talker.speak(random.choice(bamFilenames))
            self.lastBapTime = now

        woosh = base.sfxManagerList[0].getSound("weapons/machete_swing.wav", True)
        gunslinger_swing = base.sfxManagerList[0].getSound("weapons/gunslinger_swing.wav", True)
        draw = base.sfxManagerList[0].getSound("weapons/draw_wrench_engineer.wav", True)
        hits = [
            "weapons/cbar_hitbod1.wav",
            "weapons/cbar_hitbod2.wav",
            "weapons/cbar_hitbod3.wav"
        ]
        hit = base.sfxManagerList[0].getSound(random.choice(hits), True)

        woosh.set3dAttributes(self.np.getX(), self.np.getY(), self.np.getZ() + 32, 0, 0, 0)
        gunslinger_swing.set3dAttributes(self.np.getX(), self.np.getY(), self.np.getZ() + 32, 0, 0, 0)
        draw.set3dAttributes(self.np.getX(), self.np.getY(), self.np.getZ() + 32, 0, 0, 0)
        hit.set3dAttributes(self.np.getX(), self.np.getY(), self.np.getZ() + 32, 0, 0, 0)

        seq = Sequence()
        seq.append(Func(draw.play))
        seq.append(Func(woosh.play))
        seq.append(Wait(0.2))
        seq.append(Func(gunslinger_swing.play))
        seq.append(Func(hit.play))
        seq.start()

        if now - self.lastAngryTime >= 2:
            self.makeAngry()
            self.lastAngryTime = now

        self.item2Swing.play()

    def makeAngry(self):
        now = globalClock.getFrameTime()
        if now - self.lastAngryTime < 2:
            return

        def angryFade(val):
            mad = self.character.findSlider("mad")
            self.character.setSliderValue(mad, val)
            madUpper = self.character.findSlider("madUpper")
            self.character.setSliderValue(madUpper, val)

        seq = Sequence()
        seq.append(LerpFunc(angryFade, fromData=0, toData=0.65, duration=0.5, blendType='easeOut'))
        seq.append(Wait(1.0))
        seq.append(LerpFunc(angryFade, fromData=0.65, toData=0, duration=0.5, blendType='easeOut'))
        seq.start()

        self.lastAngryTime = now

    def announceGenerate(self):
        DistributedChar.announceGenerate(self)
        DistributedTFPlayerShared.announceGenerate(self)
        self.modelNp.findAllMatches("**/*robotarm_bodygroup*").hide()
        self.talker = Talker.Talker(self.modelNp, Point3(0, 0, 64), self.character, phonemes['engineer'], sentences)
        self.modelNp.setH(180)
        self.reparentTo(render)

    def disable(self):
        self.ivPos = None
        self.ivLookPitch = None
        self.ivLookYaw = None
        self.removeTask("animUpdate")
        DistributedTFPlayerShared.disable(self)
        DistributedChar.disable(self)

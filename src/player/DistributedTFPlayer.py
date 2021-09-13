
from tf.character.DistributedChar import DistributedChar
from direct.distributed2.DistributedObject import DistributedObject
from .DistributedTFPlayerShared import DistributedTFPlayerShared

from .TFClass import *
from .TFPlayerAnimState import TFPlayerAnimState

from tf.tfbase import Sounds

#from test_talker import Talker

from panda3d.core import *
from panda3d.direct import *

from direct.interval.IntervalGlobal import *

import random

#sentences = Talker.parseSentences("scripts/game_sounds_vo_phonemes.txt")

#phonemes = {}
#phonemes['engineer'] = Talker.Phonemes("expressions/player/engineer/phonemes/phonemes.txt",
#                               "expressions/player/engineer/phonemes/phonemes_weak.txt",
#                               "expressions/player/engineer/phonemes/phonemes_strong.txt")
#phonemes['soldier'] = Talker.Phonemes("expressions/player/soldier/phonemes/phonemes.txt",
#                               "expressions/player/soldier/phonemes/phonemes_weak.txt",
#                               "expressions/player/soldier/phonemes/phonemes_strong.txt")
#phonemes['demo'] = Talker.Phonemes("expressions/player/demo/phonemes/phonemes.txt",
#                               "expressions/player/demo/phonemes/phonemes_weak.txt",
#                               "expressions/player/demo/phonemes/phonemes_strong.txt")

class DistributedTFPlayer(DistributedChar, DistributedTFPlayerShared):

    def __init__(self):
        DistributedChar.__init__(self)
        DistributedTFPlayerShared.__init__(self)

        self.animState = TFPlayerAnimState(self)

        self.lastActiveWeapon = -1

        self.lastAngryTime = 0.0

        self.talker = None

        self.classInfo = None

        # Remove rotation interpolation as we do client-side rotation in
        # TFPlayerAnimState.
        self.removeInterpolatedVar(self.ivRot)

        self.ivEyeH = InterpolatedFloat()
        self.ivEyeH.setLooping(True)
        self.addInterpolatedVar(self.ivEyeH, self.getEyeH, self.setEyeH, DistributedObject.SimulationVar)
        self.ivEyeP = InterpolatedFloat()
        self.ivEyeP.setLooping(True)
        self.addInterpolatedVar(self.ivEyeP, self.getEyeP, self.setEyeP, DistributedObject.SimulationVar)

        #self.ivLookPitch = InterpolatedFloat()
        #self.ivLookPitch.setLooping(True)
        #self.addInterpolatedVar(self.ivLookPitch, self.getLookPitch, self.setLookPitch, DistributedObject.AnimationVar)

        #self.ivLookYaw = InterpolatedFloat()
        #self.ivLookYaw.setLooping(True)
        #self.addInterpolatedVar(self.ivLookYaw, self.getLookYaw, self.setLookYaw, DistributedObject.AnimationVar)

        #self.ivMoveX = InterpolatedFloat()
        #self.addInterpolatedVar(self.ivMoveX, self.getMoveX, self.setMoveX, DistributedObject.AnimationVar)

        #self.ivMoveY = InterpolatedFloat()
        #self.addInterpolatedVar(self.ivMoveY, self.getMoveY, self.setMoveY, DistributedObject.AnimationVar)

    def RecvProxy_rot(self, r, i, j, k):
        # Ignoring this because the player angles are set in TFPlayerAnimState.
        pass

    def setEyeH(self, h):
        self.eyeH = h

    def getEyeH(self):
        return self.eyeH

    def setEyeP(self, p):
        self.eyeP = p

    def getEyeP(self):
        return self.eyeP

    def playerAnimEvent(self, event):
        """
        Animation event sent by the AI.
        """
        self.animState.doAnimationEvent(event, 0)

    def setPos(self, *args, **kwargs):
        DistributedChar.setPos(self, *args, **kwargs)
        # Keep controller in sync.
        self.controller.setFootPosition(self.getPos(base.render))

    #def becomeRagdoll(self, *args, **kwargs):
    #    #self.disableController()
    #    DistributedChar.becomeRagdoll(self, *args, **kwargs)

    def respawn(self):
        # Release reference to the ragdoll.
        if self.ragdoll:
            self.ragdoll[1].setEnabled(False)
            #self.ragdoll[1].updateTask.remove()
            self.ragdoll[0].modelNp.hide()
        self.ragdoll = None
        self.show()
        #self.enableController()

    def RecvProxy_activeWeapon(self, index):
        self.setActiveWeapon(index)

    def setActiveWeapon(self, index):
        if self.activeWeapon == index:
            # Already the active one.
            return

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
        ctx.enableExtrapolation(False)
        ctx.setLastTimestamp(base.cr.lastServerTickTime)
        vel = Vec3()
        self.ivPos.getDerivativeSmoothVelocity(vel, globalClock.getFrameTime())
        q = self.getQuat(NodePath())
        q.invertInPlace()
        vel = q.xform(vel)
        return -vel

    def setLookPitch(self, pitch):
        self.lookPitch = pitch
        self.getPoseParameter("body_pitch").setNormValue(pitch)

    def getLookPitch(self):
        return self.lookPitch

    def setLookYaw(self, yaw):
        self.lookYaw = yaw
        self.getPoseParameter("body_yaw").setNormValue(yaw)

    def getLookYaw(self):
        return self.lookYaw

    def setMoveX(self, moveX):
        self.moveX = moveX
        self.getPoseParameter("move_x").setNormValue(moveX)

    def getMoveX(self):
        return self.moveX

    def setMoveY(self, moveY):
        self.moveY = moveY
        self.getPoseParameter("move_y").setNormValue(moveY)

    def getMoveY(self):
        return self.moveY

    def postDataUpdate(self):
        DistributedChar.postDataUpdate(self)
        self.classInfo = ClassInfos[self.tfClass]

        if self.activeWeapon != self.lastActiveWeapon:
            self.lastActiveWeapon = self.activeWeapon

        #print(self.position, self.lookPitch, self.lookYaw)

    def update(self):
        DistributedChar.update(self)
        self.animState.update()

    #def update(self):
    #    DistributedObject.update(self)

        #ctx = InterpolationContext()
        #ctx.enableExtrapolation(True)

        #self.prevPos = Point3(self.position)

    def speak(self, soundIndex):
        pass
        #self.talker.speak(soundIndex)

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
        #for hide in self.classInfo.Hide:
        #    self.modelNp.findAllMatches("**/*" + hide + "*").hide()
        self.viewOffset = Vec3(0, 0, self.classInfo.ViewHeight)
        #self.talker = Talker.Talker(self.modelNp, Point3(0, 0, self.classInfo.ViewHeight), self.character, phonemes[self.classInfo.Phonemes], sentences)
        #self.modelNp.setH(180)
        self.reparentTo(render)

    def disable(self):
        self.ivPos = None
        self.ivLookPitch = None
        self.ivLookYaw = None
        self.removeTask("animUpdate")
        DistributedTFPlayerShared.disable(self)
        DistributedChar.disable(self)

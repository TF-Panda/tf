
from tf.actor.DistributedChar import DistributedChar
from direct.distributed2.DistributedObject import DistributedObject
from .DistributedTFPlayerShared import DistributedTFPlayerShared

from .TFClass import *
from .TFPlayerAnimState import TFPlayerAnimState

from tf.tfbase import Sounds
from tf.actor.Eyes import Eyes
from tf.actor.Expressions import Expressions

#from test_talker import Talker

from panda3d.core import *
from panda3d.direct import *

from direct.interval.IntervalGlobal import *
from direct.directbase import DirectRender

import random
import math

sentences = SentenceCollection()
sentences.load("scripts/game_sounds_vo_phonemes.txt")

phonemes = {}

def loadClassPhonemes(clsName):
    # We need to load the model and get the character so it can map slider
    # names to slider indices.
    mdl = NodePath(Loader.getGlobalPtr().loadSync("models/char/%s" % clsName))
    char = mdl.find("**/+CharacterNode").node().getCharacter()
    phonemes[clsName] = Phonemes()
    phonemes[clsName].read(Phonemes.PCNormal, "expressions/player/%s/phonemes/phonemes.txt" % clsName, char)
    phonemes[clsName].read(Phonemes.PCStrong, "expressions/player/%s/phonemes/phonemes_strong.txt" % clsName, char)
    phonemes[clsName].read(Phonemes.PCWeak, "expressions/player/%s/phonemes/phonemes_weak.txt" % clsName, char)

phonemeClasses = [
    'engineer',
    'heavy',
    'demo',
    'soldier',
    'scout',
    'spy'
]

def loadPhonemes():
    for clsName in phonemeClasses:
        loadClassPhonemes(clsName)

loadPhonemes()

class DistributedTFPlayer(DistributedChar, DistributedTFPlayerShared):

    def __init__(self):
        DistributedChar.__init__(self)
        DistributedTFPlayerShared.__init__(self)

        self.animState = TFPlayerAnimState(self)

        self.lastActiveWeapon = -1

        self.talker = None
        self.eyes = None
        self.expressions = None

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

        self.currentSpeech = None

    def getSpatialAudioCenter(self):
        # If we're ragdolling, position spatial audio relative to
        # the root ragdoll joint.
        if self.ragdoll:
            return self.ragdoll[1].getRagdollMatrix()

        return DistributedChar.getSpatialAudioCenter(self)

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

    def playerAnimEvent(self, event, data):
        """
        Animation event sent by the AI.
        """
        self.animState.doAnimationEvent(event, data)

    def setPos(self, *args, **kwargs):
        DistributedChar.setPos(self, *args, **kwargs)
        # Keep controller in sync.
        self.controller.setFootPosition(self.getPos(base.render))

    def becomeRagdoll(self, *args, **kwargs):
        self.disableController()
        DistributedChar.becomeRagdoll(self, *args, **kwargs)
        if self.ragdoll:
            self.ragdoll[0].showThrough(DirectRender.ShadowCameraBitmask)
            # Re-direct lip-sync to ragdoll.
            if self.talker:
                self.talker.setCharacter(self.ragdoll[0].character)
        if self.eyes:
            self.eyes.disable()

    def respawn(self):
        # Release reference to the ragdoll.
        if self.ragdoll:
            self.ragdoll[1].destroy()
            self.ragdoll[0].clearModel()
            self.ragdoll[0].cleanup()
            # Return lip-sync to actual model.
            if self.talker:
                self.talker.setCharacter(self.character)
        self.ragdoll = None
        self.show()
        self.enableController()
        if self.eyes:
            self.eyes.enable()

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
        self.updateClassSpeed()

        if self.activeWeapon != self.lastActiveWeapon:
            self.lastActiveWeapon = self.activeWeapon

    def update(self):
        DistributedChar.update(self)
        self.animState.update()

    def stopSpeech(self):
        if self.talker:
            self.talker.stop()
        if self.currentSpeech:
            self.currentSpeech.stop()
            self.currentSpeech = None

    def speak(self, soundIndex):
        self.stopSpeech()

        spatial = self != base.localAvatar
        info = Sounds.AllSounds[soundIndex]
        data = Sounds.createSound(info, spatial=spatial, getWave=True)
        if not data:
            return
        sound, wave = data
        if spatial:
            self.registerSpatialSound(sound, self.viewOffset)
        self.currentSpeech = sound
        if self.talker:
            self.talker.speak(sound, sentences.getSentence(str(wave.filename)))
        sound.play()

    def onTFClassChanged(self):
        self.stopSpeech()
        if self.classInfo.Phonemes is not None:
            self.talker = CharacterTalker(self.character, phonemes[self.classInfo.Phonemes])
        else:
            self.talker = None
        if self.eyes:
            self.eyes.cleanup()
        self.eyes = Eyes(self.characterNp)
        self.eyes.headRotationOffset = self.classInfo.HeadRotationOffset
        self.eyes.enable()
        if self.expressions:
            self.expressions.cleanup()
            self.expressions = None
        if self.classInfo.Expressions is not None:
            self.expressions = Expressions(self.character, self.classInfo.Expressions)
            self.expressions.pushExpression('idle', 1.0, oscillation=0.4, oscillationSpeed=1.5)
        self.viewOffset = Vec3(0, 0, self.classInfo.ViewHeight)

    def RecvProxy_tfClass(self, tfClass):
        self.tfClass = tfClass
        self.classInfo = ClassInfos[tfClass]
        self.onTFClassChanged()

    def pushExpression(self, name):
        if self.expressions:
            if not self.expressions.hasExpression(name):
                self.expressions.pushExpression(name, 0.8, 2.5)

    def makeAngry(self):
        self.pushExpression('specialAction')

    def __updateTalker(self, task):
        if self.ragdoll:
            # Don't do this while ragdolling and the model is hidden.
            return task.cont

        if self.talker:
            self.talker.update()

        if self.expressions:
            self.expressions.update()

        return task.cont

    def announceGenerate(self):
        DistributedChar.announceGenerate(self)
        DistributedTFPlayerShared.announceGenerate(self)
        self.reparentTo(base.dynRender)
        self.addTask(self.__updateTalker, 'talker', appendTask=True, sim=False)

    def disable(self):
        if self.expressions:
            self.expressions.cleanup()
            self.expressions = None
        if self.eyes:
            self.eyes.cleanup()
            self.eyes = None
        self.stopSpeech()
        self.talker = None
        self.ivPos = None
        self.ivLookPitch = None
        self.ivLookYaw = None
        self.removeTask("animUpdate")
        self.removeTask("talker")
        DistributedTFPlayerShared.disable(self)
        DistributedChar.disable(self)

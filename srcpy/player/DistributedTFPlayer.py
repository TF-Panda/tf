
from tf.actor.DistributedChar import DistributedChar
from direct.distributed2.DistributedObject import DistributedObject
from .DistributedTFPlayerShared import DistributedTFPlayerShared

from .TFClass import *
from .TFPlayerAnimState import TFPlayerAnimState

from tf.tfbase import Sounds
from tf.actor.Eyes import Eyes
from tf.actor.Expressions import Expressions
from .PlayerGibs import PlayerGibs

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

        self.ivVel = InterpolatedVec3()
        self.addInterpolatedVar(self.ivVel, self.getVelocity, self.setVelocity, DistributedObject.SimulationVar)

        self.currentSpeech = None

        self.gibs = None

    def isPlayer(self):
        """
        Returns True if this entity is a player.  Overridden in
        DistributedTFPlayer to return True.  Convenience method
        to avoid having to check isinstance() or __class__.__name__.
        """
        return True

    def getSpatialAudioCenter(self):
        if self.ragdoll:
            # If we're ragdolling, position spatial audio relative to
            # the ragdoll head.
            return self.ragdoll[1].getJointActor("bip_head").getTransform().getMat()
        elif self.gibs:
            # Spatial sounds follow the head gib when gibbed.
            return self.gibs.getHeadMatrix()

        # Return world space transform of player + view offset.
        # Assumes no pitch or roll in angles.  Proper way would
        # be to put view offset in a translation matrix and multiply
        # node transform by that.  But since we never have pitch
        # or roll in player angles, it is faster to just add the
        # view offset onto the translation component.
        trans = self.getMat(base.render)
        trans.setRow(3, trans.getRow3(3) + self.viewOffset)
        return trans

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
        if self.controller:
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
            if self.expressions:
                self.expressions.character = self.ragdoll[0].character
                # Remove idle expression so ragdoll goes to blank face after
                # pain.
                self.expressions.clearExpression('idle')
        if self.eyes:
            self.eyes.disable()

    def gib(self):
        self.disableController()
        self.hide()
        if self.gibs:
            self.gibs.destroy()
            self.gibs = None
        cdata = self.modelNp.node().getCustomData()
        if cdata.hasAttribute("gibs"):
            gibInfo = cdata.getAttributeValue("gibs").getList()
            self.gibs = PlayerGibs(self.getPos(base.render), self.getHpr(base.render), self.skin, gibInfo)
            if self.eyes:
                self.eyes.disable()

    def isDead(self):
        return (self.playerState == self.StateDead) or DistributedChar.isDead(self)

    def respawn(self):
        # Release reference to the ragdoll.
        if self.ragdoll:
            self.ragdoll[1].destroy()
            self.ragdoll[0].delete()
            # Return lip-sync to actual model.
            if self.talker:
                self.talker.setCharacter(self.character)
            if self.expressions:
                self.expressions.character = self.character
        if self.gibs:
            self.gibs.destroy()
        self.gibs = None
        self.ragdoll = None
        self.show()
        self.enableController()
        if self.eyes:
            self.eyes.enable()
        if self.expressions:
            self.expressions.resetExpressions()
            self.expressions.pushExpression('idle', 1.0, oscillation=0.4, oscillationSpeed=1.5)

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

    #def getVelocity(self):
    #    """
    #    Returns the world-space linear velocity of the player.
    #    """

    #    ctx = InterpolationContext()
    #    ctx.enableExtrapolation(False)
    #    ctx.setLastTimestamp(base.cr.lastServerTickTime)
    #    vel = Vec3()
    #    self.ivPos.getDerivativeSmoothVelocity(vel, globalClock.getFrameTime())
        #q = self.getQuat(NodePath())
        #q.invertInPlace()
        #vel = q.xform(vel)
    #    return -vel

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

    def __updateAnimState(self, task):
        self.animState.update()
        return task.cont

    def stopSpeech(self):
        if self.talker:
            self.talker.stop()
        if self.currentSpeech:
            self.currentSpeech.stop()
            self.currentSpeech = None

    def speak(self, soundIndex):
        # This automatically stops the currently playing sound on the voice
        # channel.
        spatial = (self != base.localAvatar)
        info = Sounds.AllSounds[soundIndex]
        data = Sounds.createSound(info, spatial=spatial, getWave=True)
        if not data:
            return
        sound, wave = data
        self.soundEmitter.registerSound(sound, Sounds.Channel.CHAN_VOICE, spatial, self.viewOffset)
        self.currentSpeech = sound
        if self.talker:
            self.talker.speak(sound, sentences.getSentence(str(wave.filename)))
        sound.play()

    def onModelChanged(self):
        DistributedChar.onModelChanged(self)
        if self.animState:
            # Re-fetch pose parameters on new model.
            self.animState.onPlayerModelChanged()

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
        #if self.ragdoll:
        #    # Don't do this while ragdolling and the model is hidden.
        #    return task.cont

        if self.talker and not self.gibs:
            self.talker.update()

        if self.expressions and not self.gibs:
            self.expressions.update()

        return task.cont

    def announceGenerate(self):
        DistributedChar.announceGenerate(self)
        DistributedTFPlayerShared.announceGenerate(self)
        self.reparentTo(base.dynRender)
        self.addTask(self.__updateTalker, 'talker', appendTask=True, sim=False)
        self.addTask(self.__updateAnimState, 'playerAnimState', appendTask=True, sort=31, sim=False)

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
        self.ivVel = None
        self.removeTask("animUpdate")
        self.removeTask("talker")
        DistributedTFPlayerShared.disable(self)
        DistributedChar.disable(self)

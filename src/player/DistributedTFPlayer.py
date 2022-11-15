
from tf.actor.DistributedChar import DistributedChar
from direct.distributed2.DistributedObject import DistributedObject
from .DistributedTFPlayerShared import DistributedTFPlayerShared

from .TFClass import *
from .TFPlayerAnimState import TFPlayerAnimState

from tf.tfbase import Sounds, TFGlobals, TFEffects
from tf.actor.Eyes import Eyes
from tf.actor.Expressions import Expressions
from .PlayerGibs import PlayerGibs
from .TFPlayerState import TFPlayerState

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
    'spy',
    'medic',
    'sniper'
]

def loadPhonemes():
    for clsName in phonemeClasses:
        loadClassPhonemes(clsName)

loadPhonemes()

class DistributedTFPlayer(DistributedChar, DistributedTFPlayerShared):

    DTNone = 0
    DTRagdoll = 1
    DTGibs = 2

    def __init__(self):
        DistributedChar.__init__(self)
        DistributedTFPlayerShared.__init__(self)

        self.animState = TFPlayerAnimState(self)

        self.prevPlayerState = self.playerState

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

        self.overhealedEffect = None
        self.burningEffect = None

        self.deathType = self.DTNone

        self.gibs = None

        self.viewOffsetNode = self.attachNewNode("viewOffset")

    def startBurningEffect(self):
        self.stopBurningEffect()

        if self == base.localAvatar:
            return

        self.burningEffect = TFEffects.getPlayerFireEffect()
        self.burningEffect.setInput(0, self.modelNp, False)
        self.burningEffect.start(base.dynRender, self)

    def stopBurningEffect(self):
        if self.burningEffect:
            self.burningEffect.softStop()
            self.burningEffect = None

    def RecvProxy_condition(self, cond):
        old = self.condition
        self.condition = cond

        condChanged = old ^ cond

        added = condChanged & cond
        removed = condChanged & (~cond)

        for i in range(self.COND_COUNT):
            if added & (1 << (i + 1)):
                self.onAddCondition(i + 1)
            elif removed & (1 << (i + 1)):
                self.onRemoveCondition(i + 1)

    def onAddCondition(self, cond):
        if cond == self.CondBurning:
            self.startBurningEffect()
            if self == base.localAvatar:
                self.emitSound("Fire.Engulf")
            else:
                self.emitSoundSpatial("Fire.Engulf", (0, 0, 30))

    def onRemoveCondition(self, cond):
        if cond == self.CondBurning:
            self.stopBurningEffect()

    def doBloodGoop(self, pos):
        from tf.tfbase.TFEffects import getBloodGoopEffect
        from direct.interval.IntervalGlobal import Sequence, Wait, Func

        emitNode = base.render.attachNewNode("emitBloodGoop")
        emitNode.setPos(pos)

        effect = getBloodGoopEffect()
        effect.setInput(0, emitNode, True)
        effect.start(base.dynRender)
        Sequence(Wait(0.1), Func(effect.softStop)).start()

    def createOverhealedEffect(self):
        from tf.tfbase import TFEffects
        system = TFEffects.getOverhealedEffect(self.team)
        system.setInput(0, self.modelNp, False)
        return system

    def isPlayer(self):
        """
        Returns True if this entity is a player.  Overridden in
        DistributedTFPlayer to return True.  Convenience method
        to avoid having to check isinstance() or __class__.__name__.
        """
        return True

    def getSpatialAudioCenter(self):
        if self.deathType == self.DTNone:
            # Return world space transform of player + view offset.
            # Assumes no pitch or roll in angles.  Proper way would
            # be to put view offset in a translation matrix and multiply
            # node transform by that.  But since we never have pitch
            # or roll in player angles, it is faster to just add the
            # view offset onto the translation component.
            trans = self.getMat(base.render)
            trans.setRow(3, trans.getRow3(3) + self.viewOffset)
            return trans
        elif self.deathType == self.DTGibs and self.gibs:
            # Spatial sounds follow the head gib when gibbed.
            return self.gibs.getHeadMatrix()
        elif self.deathType == self.DTRagdoll and self.ragdoll:
            # If we're ragdolling, position spatial audio relative to
            # the ragdoll head.
            return self.ragdoll[1].getJointActor("bip_head").getTransform().getMat()

        return Mat4.identMat()

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
            self.controller.foot_position = self.getPos()

    def becomeRagdoll(self, *args, **kwargs):
        DistributedChar.becomeRagdoll(self, *args, **kwargs)
        self.deathType = self.DTRagdoll
        if self.ragdoll:
            self.ragdoll[0].modelNp.showThrough(DirectRender.ShadowCameraBitmask)
            if self.talker:
                # Play lip sync on the ragdoll as well.
                talkerIndex = self.ragdoll[0].character.addChannel(self.talker)
                self.ragdoll[0].character.loop(talkerIndex, True)
            if self.expressions:
                self.expressions.character = self.ragdoll[0].character
                # Remove idle expression so ragdoll goes to blank face after
                # pain.
                self.expressions.clearExpression('idle')

    def gib(self):
        self.deathType = self.DTGibs
        if self.gibs:
            self.gibs.destroy()
            self.gibs = None
        cdata = self.modelData
        if cdata.hasAttribute("gibs"):
            gibInfo = cdata.getAttributeValue("gibs").getList()
            self.gibs = PlayerGibs(self.getPos(base.render), self.getHpr(base.render), self.skin, gibInfo)

    def isDead(self):
        return (self.playerState != TFPlayerState.Playing) or DistributedChar.isDead(self)

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
        spatial = (self != base.localAvatar)
        info = Sounds.AllSounds[soundIndex]
        data = Sounds.createSound(info, spatial=spatial, getWave=True)
        if not data:
            return
        sound, wave = data
        self.stopSpeech()
        self.soundEmitter.registerSound(sound, Sounds.Channel.CHAN_AUTO, spatial, self.viewOffset)
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
        self.talker = None
        if self.eyes:
            self.eyes.cleanup()

        if self.overhealedEffect:
            self.overhealedEffect.stop()
            self.overhealedEffect = None

        # Load new player model.
        self.loadModel(self.classInfo.PlayerModel)
        self.setSkin(self.team)
        if self.viewModel:
            self.viewModel.loadModel(self.classInfo.ViewModel)

        if self.classInfo.Phonemes:
            # Set up the slider-based lip sync animation channel.
            self.talker = CharacterTalker(phonemes[self.classInfo.Phonemes])
            self.talker.setFlags(AnimChannel.FDelta)
            talkerIndex = self.character.addChannel(self.talker)
            self.character.loop(talkerIndex, True, 6)

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
        self.viewOffsetNode.setPos(self.viewOffset)

    def onTFTeamChanged(self):
        pass

    def RecvProxy_tfClass(self, tfClass):
        self.tfClass = tfClass
        self.classInfo = ClassInfos[tfClass]
        self.onTFClassChanged()

    def RecvProxy_team(self, team):
        if team != self.team:
            self.team = team
            self.onTFTeamChanged()

    def pushExpression(self, name):
        if self.expressions:
            if not self.expressions.hasExpression(name):
                self.expressions.pushExpression(name, 0.8, 2.5)

    def makeAngry(self):
        self.pushExpression('specialAction')

    def __updateTalker(self, task):
        if self.deathType in (self.DTNone, self.DTRagdoll):
            if self.expressions:
                self.expressions.update()

        return task.cont

    def changePlayerState(self, newState, prevState):
        if prevState == TFPlayerState.Playing:
            # Leaving the tangible world.  We died or something.
            self.disableController()
            self.removeTask('playerAnimState')
            if self.eyes:
                self.eyes.disable()
            if self.overhealedEffect:
                self.overhealedEffect.softStop()
                self.overhealedEffect = None
            self.reparentTo(base.hidden)

        if newState == TFPlayerState.Playing:
            # Entering the tangible world.
            self.deathType = self.DTNone
            self.gibs = None
            self.enableController()
            self.addTask(self.__updateAnimState, 'playerAnimState', appendTask=True, sort=31, sim=False)
            self.reparentTo(base.dynRender)
            if self.eyes:
                self.eyes.enable()
            if self.expressions:
                self.expressions.character = self.character
                self.expressions.resetExpressions()
                self.expressions.pushExpression('idle', 1.0, oscillation=0.4, oscillationSpeed=1.5)

    def postDataUpdate(self):
        DistributedChar.postDataUpdate(self)

        if self.prevPlayerState != self.playerState:
            self.changePlayerState(self.playerState, self.prevPlayerState)
            self.prevPlayerState = self.playerState

        if self.health > self.maxHealth and self != base.localAvatar:
            if not self.overhealedEffect and not self.isDead():
                self.overhealedEffect = self.createOverhealedEffect()
                self.overhealedEffect.start(base.dynRender, self)
        elif self.overhealedEffect:
            self.overhealedEffect.softStop()
            self.overhealedEffect = None

    def announceGenerate(self):
        DistributedChar.announceGenerate(self)
        DistributedTFPlayerShared.announceGenerate(self)
        self.addTask(self.__updateTalker, 'talker', appendTask=True, sim=False)

    def disable(self):
        if self.viewOffsetNode:
            self.viewOffsetNode.removeNode()
            self.viewOffsetNode = None
        if self.expressions:
            self.expressions.cleanup()
            self.expressions = None
        if self.eyes:
            self.eyes.cleanup()
            self.eyes = None
        if self.overhealedEffect:
            self.overhealedEffect.stop()
            self.overhealedEffect = None
        self.stopBurningEffect()
        self.stopSpeech()
        self.talker = None
        self.ivPos = None
        self.ivLookPitch = None
        self.ivLookYaw = None
        self.ivVel = None
        self.removeTask("playerAnimState")
        self.removeTask("talker")
        DistributedTFPlayerShared.disable(self)
        DistributedChar.disable(self)

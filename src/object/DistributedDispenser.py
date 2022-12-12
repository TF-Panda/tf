"""DistributedDispenser module: contains the DistributedDispenser class."""

from panda3d.core import *
from panda3d.pphysics import *

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.tfbase.TFGlobals import getTF2BuildFont, TFTeam, SpeechConcept
from tf.tfbase import TFLocalizer, CollisionGroups

from .BaseObject import BaseObject
from .ObjectType import ObjectType
from .ObjectState import ObjectState

DISPENSER_MAX_METAL_AMMO = 400
DISPENSER_MAX_HEALING_TARGETS = 32
DISPENSER_AMMO = 40

class DistributedDispenser(BaseObject):

    notify = directNotify.newCategory("DistributedDispenser")

    Models = [
        "models/buildables/dispenser",
        "models/buildables/dispenser_light",
    ]

    def __init__(self):
        BaseObject.__init__(self)
        self.objectType = ObjectType.Dispenser
        self.objectName = TFLocalizer.Dispenser
        self.maxHealth = 150
        self.maxLevel = 1
        self.metalToDropInGibs = 50
        self.ammoMetal = 0
        self.explodeSound = "Building_Dispenser.Explode"

        self.touchTrigger = None
        self.touchingEntities = []

        self.healingTargets = []

        self.viewOffset = Vec3(0, 0, 28)

        if IS_CLIENT:
            self.targetBeams = {}
            self.idleSound = None
            self.healSound = None
            self.text0 = None
            self.text1 = None
            self.text0Root = None
            self.text1Root = None
            self.screen0 = None
            self.screen1 = None

    if not IS_CLIENT:
        def onKilled(self, info):
            bldr = self.getBuilder()
            if bldr:
                bldr.speakConcept(SpeechConcept.ObjectDestroyed, {'objecttype': 'dispenser'})
            BaseObject.onKilled(self, info)

        def onFinishConstruction(self):
            BaseObject.onFinishConstruction(self)
            self.setModelIndex(1)

        def generate(self):
            self.setModelIndex(0)
            BaseObject.generate(self)

        def delete(self):
            if self.touchTrigger:
                self.touchTrigger.node().removeFromScene(base.physicsWorld)
                self.touchTrigger.removeNode()
                self.toughTrigger = None
            self.stopHealingAll()
            self.touchingEntities = None
            self.healingTargets = None
            BaseObject.delete(self)

        def onBecomeActive(self):
            # Put some ammo in the Dispenser.
            self.ammoMetal = 25
            BaseObject.onBecomeActive(self)

            self.nextAmmoDispense = globalClock.frame_time + 0.5

            # Create tasks to dispense and regenerate metal.
            self.addTask(self.__refill, "dispenserRefill", appendTask=True, delay=3.0)
            self.addTask(self.__dispense, "dispenserDispense", appendTask=True, delay=0.1)

            # Create the trigger volume to heal and give ammo/metal to players.
            # Mins -70, -70, 0; Maxs 70, 70, 50 converted to half extents and position offset.
            box = PhysBox(70, 70, 25)
            tshape = PhysShape(box, PhysMaterial(0, 0, 0))
            tshape.setLocalPos((0, 0, 25))
            tshape.setSimulationShape(False)
            tshape.setSceneQueryShape(False)
            tshape.setTriggerShape(True)
            tnode = PhysRigidDynamicNode("dispenserTrigger")
            tnode.addShape(tshape)
            tnode.addToScene(base.physicsWorld)
            # Player on any team because disguised enemy spies can use the
            # dispenser.
            tnode.setIntoCollideMask(CollisionGroups.Mask_Player)
            tnode.setTriggerCallback(CallbackObject.make(self.__touchTriggerCallback))
            tnode.setKinematic(True)
            self.touchTrigger = self.attachNewNode(tnode)

        def __touchTriggerCallback(self, cbdata):
            if self.isDODeleted():
                return

            node = cbdata.getOtherNode()
            if not node:
                return
            entity = node.getPythonTag("entity")
            if not entity:
                return
            if not entity.isPlayer():
                return
            if entity.team != self.team:
                return
            if cbdata.getTouchType() == PhysTriggerCallbackData.TEnter:
                # Teammate entered dispenser trigger.
                self.startTouch(entity)
            else:
                self.endTouch(entity)

        def stopHealingAll(self):
            for doId in self.healingTargets:
                do = base.air.doId2do.get(doId)
                if do and not do.isDODeleted():
                    do.stopHealing(self.getBuilder())

        def couldHealTarget(self, target):
            """
            Returns true if the given target can be healed by this dispenser.
            """

            if not target.isEntityVisible(self, CollisionGroups.World)[0]:
                # Don't have a LOS to dispenser, can't heal them.
                return False

            if target.isPlayer() and not target.isDead():

                # TODO: Enemy spy disguised as dispenser's team an be healed.

                if target.team != self.team:
                    # Not same team (or apparent team), can't heal them.
                    return False

                return True

            return False

        def startHealing(self, other):
            """
            Begins healing the indicated player.
            """
            if other.doId in self.healingTargets:
                return
            self.healingTargets.append(other.doId)
            obj_dispenser_heal_rate = 10
            # TODO: if dispenser can be upgraded, change heal reate
            # based on upgrade level.
            other.heal(self.getBuilder(), obj_dispenser_heal_rate, True)
            self.notify.debug("Started healing " + repr(other))

        def stopHealing(self, other):
            """
            Stops healing the indicated player.
            """
            if other.doId in self.healingTargets:
                self.healingTargets.remove(other.doId)
                other.stopHealing(self.getBuilder())
                self.notify.debug("Stopped healing " + repr(other))

        def isHealingTarget(self, other):
            """
            Returns true if we are currently healing this player.
            """
            return other.doId in self.healingTargets

        def startTouch(self, other):
            if other in self.touchingEntities:
                return

            self.touchingEntities.append(other)
            if not self.isHealingTarget(other) and self.couldHealTarget(other):
                self.startHealing(other)

        def endTouch(self, other):
            if other not in self.touchingEntities:
                return

            self.touchingEntities.remove(other)
            #self.healingTargets.remove(other.doId)
            self.stopHealing(other)

        def __refill(self, task):
            # Auto refill half the amount as TFC, but twice as often.
            if self.ammoMetal < DISPENSER_MAX_METAL_AMMO:
                self.ammoMetal = int(min(self.ammoMetal + DISPENSER_MAX_METAL_AMMO * 0.1, DISPENSER_MAX_METAL_AMMO))
                self.emitSoundSpatial("Building_Dispenser.GenerateMetal")

            task.delayTime = 6.0
            return task.again

        def __dispense(self, task):
            if self.nextAmmoDispense <= globalClock.frame_time:
                numNearbyPlayers = 0
                origin = self.getPos() + (0, 0, 32)
                for plyr in base.game.playersByTeam[self.team]:
                    if plyr.isDead():
                        continue
                    if ((plyr.getPos() + (0, 0, 32)) - origin).length() > 64.0:
                        continue
                    self.dispenseAmmo(plyr)
                    numNearbyPlayers += 1
                self.nextAmmoDispense = globalClock.frame_time
                # Try to dispense more often when no players are around so we
                # give it as soon as possible when a new player shows up.
                self.nextAmmoDispense += 1.0 if (numNearbyPlayers > 0) else 0.1

            for do in list(self.touchingEntities):

                if do.isDODeleted() or do.isDead():
                    self.endTouch(do)
                    continue

                healingTarget = do.doId in self.healingTargets
                validHealingTarget = self.couldHealTarget(do)

                if healingTarget and not validHealingTarget:
                    self.stopHealing(do)
                elif not healingTarget and validHealingTarget:
                    self.startHealing(do)

            task.delayTime = 0.1
            return task.again

        def dispenseAmmo(self, ent):
            gaveAny = False

            # Give ammo.
            for wpn in ent.weapons:
                wpn = base.air.doId2do.get(wpn)
                if not wpn:
                    continue
                if not wpn.usesAmmo or wpn.ammo >= wpn.maxAmmo:
                    continue
                maxToGive = max(0, wpn.maxAmmo - wpn.ammo)
                wpn.ammo += min(maxToGive, DISPENSER_AMMO)

                if maxToGive > 0:
                    gaveAny = True

            # Give metal if class uses it.
            if ent.usesMetal():
                dispenserMetal = min(DISPENSER_AMMO, self.ammoMetal)
                maxToGive = max(0, ent.maxMetal - ent.metal)
                giveMetal = min(maxToGive, dispenserMetal)
                ent.metal += giveMetal
                self.ammoMetal -= giveMetal
                if giveMetal > 0:
                    gaveAny = True

            if gaveAny:
                ent.emitSound("BaseCombatCharacter.AmmoPickup", client=ent.owner)

            return gaveAny

    else:
        def makeHealBeamParticle(self, target):
            healBeamTargetNode = target.attachNewNode("healTargetDispenser")
            healBeamTargetNode.setPos(0, 0, 48)

            from tf.tfbase import TFEffects
            sys = TFEffects.getDispenserHealBeam(self.team)
            sys.setInput(0, self.healBeamSourceNode, False) # medigun muzzle
            sys.setInput(1, healBeamTargetNode, True) # heal target

            return sys

        def playIdleSound(self):
            self.stopIdleSound()
            self.idleSound = self.emitSoundSpatial("Building_Dispenser.Idle", loop=True)

        def stopIdleSound(self):
            if self.idleSound:
                self.idleSound.stop()
                self.idleSound = None

        def destroyScreens(self):
            if self.screen0:
                self.screen0.removeNode()
                self.screen0 = None
            if self.text0Root:
                self.text0Root.removeNode()
                self.text0Root = None
            self.text0 = None
            if self.screen1:
                self.screen1.removeNode()
                self.screen1 = None
            if self.text1Root:
                self.text1Root.removeNode()
                self.text1Root = None
            self.text1 = None

        def screenColor(self):
            if self.team == 0:
                return (0.9, 0.3, 0.3, 1)
            else:
                return (0.5, 0.75, 1, 1)

        def textColor(self):
            return (0.3, 0.3, 0.3, 1)

        def createScreen(self, index):
            root = self.find("**/dispenserRoot")

            screenMat = SourceMaterial("dispScreen")
            screenMat.setParam(MaterialParamBool("selfillum", True))

            #ll = self.find("**/controlpanel%i_ll" % index).getTransform()
            #llpos = ll.getPos()
            #llhpr = ll.getHpr()
            #ur = self.find("**/controlpanel%i_ur" % index).getTransform()
            #urpos = ur.getPos()
            #urhpr = ur.getHpr()
            if index == 0:
                llpos = Point3(-10, 36.74, 7)
                urpos = Point3(10, 47.74, 7)
            elif index == 1:
                llpos = Point3(10, 36.74, -7)
                urpos = Point3(-10, 47.74, -7)
            cm = CardMaker("cm")
            cm.setFrame(llpos.x, urpos.x, llpos.y, urpos.y)
            screenFrame = root.attachNewNode(cm.generate())
            screenFrame.setColor(self.screenColor())
            screenFrame.setZ((llpos.z + urpos.z) * 0.5)
            screenFrame.setP(-90)
            screenFrame.setMaterial(screenMat)
            text = TextNode('text')
            text.setFont(getTF2BuildFont())
            text.setTextColor(0.3, 0.3, 0.3, 1.0)
            text.setAlign(TextNode.ACenter)
            text.setText(str(self.ammoMetal))
            textRootNp = root.attachNewNode("textRoot")
            textRootNp.setPos((llpos + urpos) * 0.5)
            textRootNp.setDepthOffset(1)
            textRootNp.setScale(4)
            if index == 1:
                textRootNp.setP(90)
                textRootNp.setH(180)
            else:
                textRootNp.setP(-90)
            textRootNp.attachNewNode(text.generate())
            return (screenFrame, textRootNp, text)

        def createScreens(self):
            self.destroyScreens()

            self.screen0, self.text0Root, self.text0 = self.createScreen(0)
            self.screen1, self.text1Root, self.text1 = self.createScreen(1)

        def generate(self):
            BaseObject.generate(self)
            self.healBeamSourceNode = self.attachNewNode("HealBeamSourceNode")
            self.healBeamSourceNode.setPos(self.viewOffset)
            self.healBeamSourceNode.setH(90)

        def disable(self):
            for beam in self.targetBeams.values():
                beam.stop()
            self.targetBeams = None
            self.healBeamSourceNode = None
            self.destroyScreens()
            self.stopIdleSound()
            self.stopHealSound()
            self.healingTargets = None
            BaseObject.disable(self)

        def RecvProxy_ammoMetal(self, metal):
            if metal != self.ammoMetal:
                if self.text0:
                    self.text0.setText(str(metal))
                    self.text0Root.node().removeAllChildren()
                    self.text0Root.attachNewNode(self.text0.generate())
                if self.text1:
                    self.text1.setText(str(metal))
                    self.text1Root.node().removeAllChildren()
                    self.text1Root.attachNewNode(self.text1.generate())
                self.ammoMetal = metal

        def RecvProxy_objectState(self, state):
            BaseObject.RecvProxy_objectState(self, state)
            if state == ObjectState.Active:
                self.playIdleSound()
                self.createScreens()
            else:
                self.stopIdleSound()

        def startTargetHealBeam(self, doId):
            target = base.cr.doId2do.get(doId)
            if target:
                self.targetBeams[doId] = self.makeHealBeamParticle(target)
                self.targetBeams[doId].start(base.dynRender)

        def stopTargetHealBeam(self, doId):
            if doId in self.targetBeams:
                self.targetBeams[doId].softStop()
                del self.targetBeams[doId]

        def RecvProxy_healingTargets(self, targets):
            if len(targets) > 0:
                diff = len(targets) - len(self.healingTargets)
                if diff > 0:
                    # If we have more targets than before, we
                    # started healing new target(s), so restart heal
                    # sound.
                    self.playHealSound()
                else:
                    # We have less heal targets than before, if any target
                    # in new list is not in prev list, we started healing
                    # a new target, so restart heal sound.
                    for i in range(len(targets)):
                        if targets[i] not in self.healingTargets:
                            self.playHealSound()
                            break
            else:
                # No heal targets, stop heal sound.
                self.stopHealSound()

            added = [x for x in targets if x not in self.healingTargets]
            removed = [x for x in self.healingTargets if x not in targets]

            self.notify.debug("added heal targets " + repr(added))
            self.notify.debug("removed heal targets " + repr(removed))

            for new in added:
                self.startTargetHealBeam(new)
            for old in removed:
                self.stopTargetHealBeam(old)

            self.healingTargets = targets

        def stopHealSound(self):
            if self.healSound:
                self.healSound.stop()
                self.healSound = None

        def playHealSound(self):
            self.healSound = self.emitSoundSpatial("Building_Dispenser.Heal", (0, 0, 32), loop=True)

if not IS_CLIENT:
    DistributedDispenserAI = DistributedDispenser
    DistributedDispenserAI.__name__ = 'DistributedDispenserAI'

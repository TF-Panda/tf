
if IS_CLIENT:
    from direct.distributed2.DistributedObject import DistributedObject
    BaseClass = DistributedObject
else:
    from direct.distributed2.DistributedObjectAI import DistributedObjectAI
    BaseClass = DistributedObjectAI

from panda3d.core import *
from panda3d.pphysics import *
from panda3d.tf import PredictedObject, PredictionField, PredictionCopy

from tf.actor.Actor import Actor
from tf.tfbase.TFGlobals import WorldParent, getWorldParent, TakeDamage, Contents, CollisionGroup, SolidShape, SolidFlag, angleMod
from tf.weapon.TakeDamageInfo import addMultiDamage, applyMultiDamage, TakeDamageInfo, clearMultiDamage, calculateBulletDamageForce
from tf.tfbase import TFFilters, Sounds
from tf.tfbase.SurfaceProperties import SurfaceProperties, SurfacePropertiesByPhysMaterial
from tf.tfbase.SoundEmitter import SoundEmitter
from direct.directbase import DirectRender

if IS_CLIENT:
    from tf.player.Prediction import *
else:
    from .EntityConnectionManager import EntityConnectionManager, OutputConnection

class DistributedEntity(BaseClass, NodePath):

    def __init__(self, dynamicLighting=True):
        BaseClass.__init__(self)
        if not self.this:
            NodePath.__init__(self, "entity")

        self.hitBoxes = []

        # Are we allowed to take damage?
        self.takeDamageMode = TakeDamage.Yes

        self.velocity = Vec3(0)
        self.gravity = 1.0
        self.waterLevel = 0
        self.baseVelocity = Vec3(0)

        # The team affiliation of the entity.  This is where a pluggable
        # component system would come in handy.  We could allow entities/DOs
        # to contain components that add new data/functionality onto an
        # entity that needs it, without having to modify the base class for
        # all entities.
        self.team = -1

        # Another thing that could be done with components.  Surely, not all
        # entities need health.
        self.health = 0
        self.maxHealth = 0

        self.playerSimulated = False

        # DoId of our parent entity, or world parent code.  >= 0 is a parent
        # entity doId, < 0 is a world parent code.  A world parent is a scene
        # node instead of an entity (like render or camera).
        self.parentEntityId = WorldParent.DynRender
        # Handle to the actual parent entity or node.
        self.parentEntity = base.hidden

        self.viewOffset = Vec3()

        # Collision stuff
        self.collisionGroup = CollisionGroup.Empty
        self.contentsMask = Contents.Solid
        self.solidMask = Contents.Solid
        self.solidShape = SolidShape.Empty
        self.solidFlags = SolidFlag.Intangible
        self.mass = -1
        self.damping = 0.0
        self.rotDamping = 0.0
        self.kinematic = True
        self.hasCollisions = False
        self.triggerCallback = False
        self.contactCallback = False
        self.sleepCallback = False
        self.hullMins = Point3(0)
        self.hullMaxs = Point3(0)
        self.triggerFudge = Vec3(0)

        self.teleportParity = 0

        self.className = ""
        self.targetName = ""

        if IS_CLIENT:
            # Makes the node compute its lighting state from the lighting
            # information in the level when its rendered.
            if dynamicLighting:
                self.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
            # And render into shadow maps.
            self.showThrough(DirectRender.ShadowCameraBitmask)

            # Setting to 255 makes the entity teleport to initial transform.
            self.lastTeleportParity = 255

            # Prediction-related variables.
            self.pred = None
            self.predictionInitialized = False
            self.simulationTick = -1

            # Add interpolators for transform state of the entity/node.
            self.ivPos = InterpolatedVec3()
            self.addInterpolatedVar(self.ivPos, self.getPos, self.setPos)
            self.ivRot = InterpolatedQuat()
            self.addInterpolatedVar(self.ivRot, self.getQuat, self.setQuat)
            self.ivScale = InterpolatedVec3()
            #self.addInterpolatedVar(self.ivScale, self.getScale, self.setScale)

            self.soundEmitter = SoundEmitter(self)

        else:
            self.connMgr = EntityConnectionManager(self)
            self.parentEntityName = ""

        # Create a root node for all physics objects to live under, and hide
        # it.  This can improve cull traverser performance since it only has
        # to consider visiting the root node instead of every individual
        # physics node.
        #self.physicsRoot = self.attachNewNode("physics")
        #self.physicsRoot.node().setOverallHidden(True)
        #self.physicsRoot.node().setFinal(True)

        # Add a tag on our node that links back to us.
        self.setPythonTag("entity", self)
        self.setPythonTag("object", self)

        #self.reparentTo(self.parentEntity)

    def announceGenerate(self):
        BaseClass.announceGenerate(self)
        if IS_CLIENT:
            self.updateParentEntity()
        else:
            if self.parentEntityName:
                parentEnt = base.entMgr.targetName2ent.get(self.parentEntityName)
                if parentEnt is not None:
                    self.setParentEntityId(parentEnt.doId)
            else:
                self.updateParentEntity()


    def generate(self):
        BaseClass.generate(self)
        # Make the node for this entity recognizable.  Assign the top-level class
        # name followed by the doId.
        self.node().setName(self.uniqueName(self.__class__.__name__))
        # Don't let Actor override the name.
        self.gotName = 1

    def isPlayer(self):
        """
        Returns True if this entity is a player.  Overridden in
        DistributedTFPlayer to return True.  Convenience method
        to avoid having to check isinstance() or __class__.__name__.
        """
        return False

    def isObject(self):
        """
        Returns True if this entity is a building, such as a Sentry
        or Dispenser.  Overriden in BaseObject to return True.
        Convenience method to avoid having to check isinstance() or
        __class__.__name__.
        """
        return False

    def isDead(self):
        """
        Returns true if the entity's health is depleted, which would mean it
        is dead.
        """
        # We can't be dead if we don't have any health to begin with.
        return self.maxHealth > 0 and self.health <= 0

    def shouldCollide(self, collisionGroup, contentsMask):
        return True

    def onTriggerEnter(self, entity):
        pass

    def onTriggerExit(self, entity):
        pass

    def __triggerCallback(self, cbdata):
        # This hack checks that the DistributedObject hasn't been deleted
        # before processing this callback.  There are cases where a physics
        # callback results in the deletion of objects, but the callback may
        # be triggered multiple times in the same physics update.
        if self.isDODeleted():
            return

        np = NodePath(cbdata.getOtherNode())
        entity = np.getPythonTag("entity")
        if not entity:
            return
        if not entity.shouldCollide(self.collisionGroup, self.solidMask):
            return
        #print(entity.__class__.__name__, "enters trigger")
        if cbdata.getTouchType() == PhysTriggerCallbackData.TEnter:
            self.onTriggerEnter(entity)
        else:
            self.onTriggerExit(entity)

    def onContactStart(self, entity, pair, shape):
        pass

    def onContactEnd(self, entity, pair, shape):
        pass

    def __contactCallback(self, cbdata):
        # This hack checks that the DistributedObject hasn't been deleted
        # before processing this callback.  There are cases where a physics
        # callback results in the deletion of objects, but the callback may
        # be triggered multiple times in the same physics update.
        if self.isDODeleted():
            return

        other = cbdata.getActorA()
        otherIsB = False
        if other == self.node():
            other = cbdata.getActorB()
            otherIsB = True

        np = NodePath(other)
        entity = np.getNetPythonTag("entity")
        if not entity:
            return

        for i in range(cbdata.getNumContactPairs()):
            pair = cbdata.getContactPair(i)
            shape = pair.getShapeB() if otherIsB else pair.getShapeA()
            if pair.isContactType(PhysEnums.CTFound):
                self.onContactStart(entity, pair, shape)
            elif pair.isContactType(PhysEnums.CTLost):
                self.onContactEnd(entity, pair, shape)

    def onWake(self):
        pass

    def onSleep(self):
        pass

    def __sleepCallback(self, cbdata):
        # This hack checks that the DistributedObject hasn't been deleted
        # before processing this callback.  There are cases where a physics
        # callback results in the deletion of objects, but the callback may
        # be triggered multiple times in the same physics update.
        if self.isDODeleted():
            return

        if cbdata.isAwake():
            self.onWake()
        else:
            self.onSleep()

    def destroyCollisions(self, replaceWithNormalNode=True):
        if not self.hasCollisions or not isinstance(self.node(), PhysRigidActorNode):
            # There's no collisions.
            return

        # Ensure it's not in any PhysScene.
        self.node().removeFromScene(base.physicsWorld)

        self.removeTask("physSync")

        if replaceWithNormalNode:
            # Replace the physics node with a regular PandaNode.
            entNode = PandaNode("entity")
            entNode.replaceNode(self.node())
        self.hasCollisions = False

    def makeModelCollisionShape(self):
        return None

    def getModelSurfaceProp(self):
        return "default"

    def makeCollisionShape(self, trigger=False):
        if self.solidShape == SolidShape.Model:
            return self.makeModelCollisionShape()
        elif self.solidShape == SolidShape.Box:
            mins = Point3(self.hullMins)
            maxs = Point3(self.hullMaxs)
            if trigger:
                # User can specify a fudge for the identical trigger
                # shape so the solid shape doesn't block trigger entry.
                mins -= self.triggerFudge
                maxs += self.triggerFudge
            hx = (maxs[0] - mins[0]) / 2
            hy = (maxs[1] - mins[1]) / 2
            hz = (maxs[2] - mins[2]) / 2
            cx = (mins[0] + maxs[0]) / 2
            cy = (mins[1] + maxs[1]) / 2
            cz = (mins[2] + maxs[2]) / 2
            box = PhysBox(hx, hy, hz)
            mat = SurfaceProperties[self.getModelSurfaceProp()].getPhysMaterial()
            shape = PhysShape(box, mat)
            shape.setLocalPos((cx, cy, cz))
            return ((shape, box),)
        else:
            return None

    def setSolidMask(self, mask):
        self.solidMask = mask
        if self.hasCollisions:
            self.node().setSolidMask(mask)

    def setCollisionGroup(self, group):
        self.collisionGroup = group
        if self.hasCollisions:
            self.node().setCollisionGroup(group)

    def setContentsMask(self, mask):
        self.contentsMask = mask
        if self.hasCollisions:
            self.node().setContentsMask(mask)

    def setKinematic(self, flag):
        self.kinematic = flag
        if self.hasCollisions:
            self.node().setKinematic(flag)
            self.node().wakeUp()

    def setMass(self, mass):
        self.mass = mass
        if self.hasCollisions:
            self.node().setMass(mass)

    def initializeCollisions(self):
        if self.hasCollisions:
            self.destroyCollisions()

        if self.solidShape == SolidShape.Empty:
            return

        body = PhysRigidDynamicNode(self.node().getName())
        body.setCollisionGroup(self.collisionGroup)
        body.setContentsMask(self.contentsMask)
        body.setSolidMask(self.solidMask)
        body.setKinematic(self.kinematic)

        shapeDatas = self.makeCollisionShape()
        if not shapeDatas:
            return
        for shape, _ in shapeDatas:
            shape.setSceneQueryShape(True)
            if self.solidFlags & SolidFlag.Tangible:
                shape.setSimulationShape(True)
                shape.setTriggerShape(False)
            elif self.solidFlags & SolidFlag.Trigger:
                shape.setSimulationShape(False)
                shape.setSceneQueryShape(False)
                shape.setTriggerShape(True)
            else:
                shape.setSimulationShape(False)
                shape.setTriggerShape(False)
            body.addShape(shape)

        #body.computeMassProperties()

        if self.mass != -1:
            body.setMass(self.mass)
        body.setLinearDamping(self.damping)
        body.setAngularDamping(self.rotDamping)

        if (self.solidFlags & SolidFlag.Tangible) and \
            (self.solidFlags & SolidFlag.Trigger):
            # Add an identical shape for trigger usage only.
            tshapeDatas = self.makeCollisionShape(trigger=True)
            for tshape, _ in tshapeDatas:
                tshape.setSceneQueryShape(False)
                tshape.setSimulationShape(False)
                tshape.setTriggerShape(True)
                body.addShape(tshape)

        if (self.solidFlags & SolidFlag.Trigger) and self.triggerCallback:
            body.setTriggerCallback(CallbackObject.make(self.__triggerCallback))

        if (self.solidFlags & SolidFlag.Tangible) and self.contactCallback:
            body.setContactCallback(CallbackObject.make(self.__contactCallback))

        if not self.kinematic and self.sleepCallback:
            clbk = CallbackObject.make(self.__sleepCallback)
            body.setWakeCallback(clbk)
            body.setSleepCallback(clbk)

        if not self.kinematic:
            body.setCcdEnabled(True)
        body.addToScene(base.physicsWorld)
        # Make this the node that represents the entity.
        body.replaceNode(self.node())
        self.node().syncTransform()

        self.hasCollisions = True

        self.considerPhysSyncTask()

    def getEyePosition(self):
        return self.getPos() + self.viewOffset

    def getWorldSpaceCenter(self):
        return self.getPos(NodePath()) + (self.viewOffset * 0.5)

    def fireBullets(self, info):
        clearMultiDamage()

        # FIXME: horrible
        for do in base.net.doId2do.values():
            if isinstance(do, Actor):
                do.syncHitBoxes()

        # Fire a bullet (ignoring the shooter).
        start = info['src']
        #end = start + info['dirShooting'] * info['distance']
        result = PhysRayCastResult()
        filter = TFFilters.TFQueryFilter(self)
        base.physicsWorld.raycast(result, start, info['dirShooting'], info['distance'],
                                  BitMask32(Contents.HitBox | Contents.Solid | Contents.AnyTeam), BitMask32.allOff(),
                                  CollisionGroup.Empty, filter)
        if result.hasBlock():
            # Bullet hit something!
            block = result.getBlock()

            if not IS_CLIENT:
                if self.owner is not None:
                    exclude = [self.owner]
                else:
                    exclude = []
                base.air.game.d_doTracers(info['tracerOrigin'], [block.getPosition()], excludeClients=exclude)
            else:
                base.game.doTracer(info['tracerOrigin'], block.getPosition())

            actor = block.getActor()
            if actor:
                entity = actor.getPythonTag("entity")
            else:
                entity = None
            if not entity:
                # Didn't hit an entity.  Hmm.
                return

            #if doEffects:
                # TODO
            #    pass

            # Play bullet impact sound for material we hit.
            if not IS_CLIENT:
                physMat = block.getMaterial()
                surfaceDef = SurfacePropertiesByPhysMaterial.get(physMat)
                if not surfaceDef:
                    surfaceDef = SurfaceProperties['default']

                if entity.owner is not None:
                    # Make it non-spatialized for the client who got hit.
                    entity.emitSound(surfaceDef.bulletImpact, client=entity.owner)
                    base.world.emitSoundSpatial(surfaceDef.bulletImpact, block.getPosition(), chan=Sounds.Channel.CHAN_STATIC, excludeClients=[entity.owner])
                else:
                    # Didn't hit a player entity, spatialize for all.
                    base.world.emitSoundSpatial(surfaceDef.bulletImpact, block.getPosition(), chan=Sounds.Channel.CHAN_STATIC)

            if not IS_CLIENT:
                # Server-specific.
                dmgInfo = TakeDamageInfo()
                dmgInfo.inflictor = self
                dmgInfo.attacker = info.get('attacker', self)
                dmgInfo.setDamage(info['damage'])
                dmgInfo.damageType = info['damageType']
                dmgInfo.customDamage = info.get('customDamageType', -1)
                calculateBulletDamageForce(dmgInfo, Vec3(info['dirShooting']), block.getPosition(), 1.0)
                wasAlive = entity.health > 0
                entity.dispatchTraceAttack(dmgInfo, info['dirShooting'], block)
                applyMultiDamage()
                if wasAlive and entity.health <= 0:
                    self.onKillEntity(entity)

    if IS_CLIENT:
        #
        # Prediction-related methods.
        #

        def shouldPredict(self):
            return False

        def addPredictionFields(self):
            """
            Called when initializing an entity for prediction.

            This method should define fields that should be predicted
            for this entity.
            """

            self.addPredictionField("velocity", Vec3, tolerance=0.5)
            self.addPredictionField("team", int)
            self.addPredictionField("pos", Point3, getter=self.getPos, setter=self.setPos, tolerance=0.02)
            self.addPredictionField("hpr", Vec3, getter=self.getHpr, setter=self.setHpr, noErrorCheck=True)
            self.addPredictionField("baseVelocity", Vec3, tolerance=0.5)
            self.addPredictionField("gravity", float, networked=False)

        def initPredictable(self):
            if self.predictionInitialized:
                return

            self.pred = PredictedObject(self)

            # Mark as predictable.
            self.setPredictable(True)
            base.net.prediction.addPredictable(self)

            # Setup prediction fields.  Used to be in constructor,
            # but now deferred to prediction initialization so
            # non-predicted entities don't have to waste time setting
            # up prediction fields.
            self.addPredictionFields()

            self.pred.calcBufferSize()

            self.pred.postNetworkDataReceived(0, 0)

            for i in range(PREDICTION_DATA_SLOTS):
                # Now fill everything
                self.pred.saveData(i, PredictionCopy.CM_everything)

            self.predictionInitialized = True

        def shutdownPredictable(self):
            if not self.predictionInitialized:
                return
            base.net.prediction.removePredictable(self)
            self.setPredictable(False)
            self.predictionInitialized = False
            self.pred.cleanup()
            self.pred = None

        def setPredictable(self, flag):
            self.predictable = flag
            self.updateInterpolationAmount()

        def addPredictionField(self, name, type, getter = None, setter = None, private = False, networked = True,
                               noErrorCheck = False, tolerance = 0.0):
            assert self.pred
            flags = 0
            if private:
                flags |= PredictionField.F_private
            if networked:
                flags |= PredictionField.F_networked
            if noErrorCheck:
                flags |= PredictionField.F_no_error_check
            if type == int:
                t = PredictionField.T_int
            elif type == bool:
                t = PredictionField.T_bool
            elif type == float:
                t = PredictionField.T_float
            elif type in (Vec2, Point2):
                t = PredictionField.T_vec2
            elif type in (Vec3, Point3):
                t = PredictionField.T_vec3
            elif type in (Vec4, Point4, Quat):
                t = PredictionField.T_vec4
            else:
                assert False
            f = PredictionField(name, t, flags)
            if getter:
                f.getter = getter
            if setter:
                f.setter = setter
            f.tolerance = tolerance
            self.pred.addField(f)

        def removePredictionField(self, name):
            assert self.pred
            self.pred.removeField(name)

        def onPostRestoreData(self):
            pass

        def postDataUpdate(self):
            DistributedObject.postDataUpdate(self)

            predict = self.shouldPredict()
            if predict and not self.predictionInitialized:
                # Entity should be predicted and we haven't initialized yet.
                self.initPredictable()
            elif not predict and self.predictionInitialized:
                # Entity is no longer being predicted.
                self.shutdownPredictable()

            if self.teleportParity != self.lastTeleportParity:
                # Teleport to new position and rotation.
                self.ivPos.reset(self.getPos())
                self.ivRot.reset(self.getQuat())
                self.lastTeleportParity = self.teleportParity

    def getVelocity(self):
        return self.velocity

    def setVelocity(self, vel):
        self.velocity = vel

    #def getPhysicsRoot(self):
    #    """
    #    Returns the physics root node of the entity; the node that all physics
    #    nodes live under.
    #    """
    #    return self.physicsRoot

    def getParentEntity(self):
        return self.parentEntity

    def getParentEntityId(self):
        return self.parentEntityId

    def getHealth(self):
        return self.health

    def getMaxHealth(self):
        return self.maxHealth

    def getTeam(self):
        return self.team

    def parentChanged(self):
        """
        Called when the parent of the entity has changed.
        """
        pass

    def considerPhysSyncTask(self):
        """
        Determines whether or not a task that syncs this entity's
        physics object with its current position every frame is necessary.

        It is necessary if the entity is parented to another entity and has
        kinematic physics.
        """

        if self.parentEntityId >= 0 and self.parentEntity and self.hasCollisions and self.kinematic:
            self.addTask(self.__physSync, "physSync", sim=True, appendTask=True)
        else:
            self.removeTask("physSync")

    def __physSync(self, task):
        """
        Synchronizes the entity's net transform with its associated physics object
        every frame.
        """
        self.node().syncTransform()
        return task.cont

    def updateParentEntity(self):
        parentId = self.parentEntityId
        if parentId < 0:
            # It's a world parent.
            parentNode = getWorldParent(parentId)
            # If the world parent is None, don't change the current
            # parent.
            if parentNode is not None:
                self.wrtReparentTo(parentNode)
            self.parentEntity = parentNode
        else:
            # Should be an entity parent.
            parentEntity = base.net.doId2do.get(parentId)
            if parentEntity is not None:
                self.wrtReparentTo(parentEntity)
            else:
                # If parent entity not found, parent to hidden.  Better
                # idea than parenting to render and having the model
                # just float in space or something.
                self.wrtReparentTo(base.hidden)
            self.parentEntity = parentEntity

        self.considerPhysSyncTask()

    def setParentEntityId(self, parentId):
        """
        Sets the parent of this entity.  Parent is referred to by doId.  Can
        also be a world parent code, in which case the entity will be parented
        to the associated scene graph node instead of an entity.
        """

        if parentId != self.parentEntityId:
            self.parentEntityId = parentId
            self.updateParentEntity()
            self.parentChanged()

    if IS_CLIENT:
        ###########################################################################
        # These receive proxies apply the received transforms directly to our
        # node.

        def RecvProxy_pos(self, x, y, z):
            self.setPos((x, y, z))

        def RecvProxy_rot(self, r, i, j, k):
            self.setQuat((r, i, j, k))

        def RecvProxy_scale(self, x, y, z):
            self.setScale((x, y, z))

        def RecvProxy_parentEntityId(self, parentId):
            # If the parent changed, reset our transform interp vars.
            if parentId != self.parentEntityId:
                self.ivPos.reset(self.getPos())
                self.ivRot.reset(self.getQuat())
                self.ivScale.reset(self.getScale())
                self.setParentEntityId(parentId)

        def RecvProxy_velocity(self, x, y, z):
            self.velocity = Vec3(x, y, z)

        ###########################################################################
    else: # SERVER

        def SendProxy_pos(self):
            return self.getPos()

        def SendProxy_rot(self):
            return self.getQuat()

        def SendProxy_scale(self):
            return self.getScale()

        def teleport(self):
            """
            Makes the client teleport the entity to the current server position
            the next time it receives a state update for this entity.
            """
            self.teleportParity += 1
            self.teleportParity %= 256

    if not IS_CLIENT:
        def initFromLevel(self, ent, properties):
            """
            Called to initialize the level entity from the given property
            structure.
            """
            self.className = ent.getClassName()
            if properties.hasAttribute("origin"):
                origin = Vec3()
                properties.getAttributeValue("origin").toVec3(origin)
                self.setPos(origin)
            if properties.hasAttribute("angles"):
                angles = Vec3()
                properties.getAttributeValue("angles").toVec3(angles)
                self.setHpr(angles[1] - 90, -angles[0], angles[2])
            if properties.hasAttribute("targetname"):
                self.targetName = properties.getAttributeValue("targetname").getString()
                if self.targetName:
                    base.entMgr.registerEntity(self)
            if properties.hasAttribute("TeamNum"):
                self.team = properties.getAttributeValue("TeamNum").getInt() - 2
            if properties.hasAttribute("parentname"):
                self.parentEntityName = properties.getAttributeValue("parentname").getString()

            for i in range(ent.getNumConnections()):
                conn = ent.getConnection(i)
                oconn = OutputConnection()
                # Convert wildcards to python regex wildcard.
                oconn.targetEntityName = conn.getTargetName().replace("*", ".+")
                oconn.inputName = conn.getInputName()
                oconn.once = conn.getRepeat()
                oconn.delay = conn.getDelay()
                for j in range(conn.getNumParameters()):
                    param = conn.getParameter(j)
                    if param:
                        oconn.parameters.append(param)
                self.connMgr.addConnection(conn.getOutputName(), oconn)

        def takeDamage(self, info):

            # TODO: Damage filter

            #if not base.game.allowDamage(self, info):
            #    return

            self.onTakeDamage(info)

        def onTakeDamage(self, info):
            if self.hasCollisions and not self.kinematic:
                # Apply the damage force to the physics-simulated body.
                self.node().addForce(info.damageForce, self.node().FTImpulse)

        def emitSound(self, soundName, volume=None, loop=False, chan=None, client=None, excludeClients=[]):
            soundInfo = Sounds.createSoundServer(soundName)
            if soundInfo is None:
                return

            if volume is not None:
                # Overriding volume.
                soundInfo[2] = volume

            if chan is not None:
                # Overriding sound channel.
                soundInfo[4] = chan

            soundInfo.append(loop)

            self.sendUpdate('emitSound_sv', soundInfo, client=client, excludeClients=excludeClients)

        def emitSoundSpatial(self, soundName, offset=(0, 0, 2), volume=None, loop=False, chan=None, client=None, excludeClients=[]):
            soundInfo = Sounds.createSoundServer(soundName)
            if soundInfo is None:
                return
            if volume is not None:
                soundInfo[2] = volume
            if chan is not None:
                soundInfo[4] = chan
            soundInfo.append(offset)
            soundInfo.append(loop)
            self.sendUpdate('emitSoundSpatial_sv', soundInfo, client=client, excludeClients=excludeClients)

        def isEntityVisible(self, entity, traceMask):
            """
            Traces a line from this entity's position to the indicated
            coordinate or entity.  If the input is a coordinate, returns True
            if the line traced to the coordinate without being blocked.  If the
            input is an entity, returns True if the line traced to the entity
            without being blocked.  If there was a block, the blocking entity
            is returned as the second return value in a tuple.
            """

            lookerOrigin = self.getEyePosition()
            targetOrigin = entity.getEyePosition()
            dir = targetOrigin - lookerOrigin
            dist = dir.length()
            dir.normalize()
            filter = PhysQueryNodeFilter(self, PhysQueryNodeFilter.FTExclude)
            result = PhysRayCastResult()
            base.physicsWorld.raycast(result, lookerOrigin, dir, dist,
                                      traceMask, 0, 0, filter)
            if result.hasBlock():
                block = result.getBlock()
                node = block.getActor()
                if node:
                    np = NodePath(node)
                    ent = np.getNetPythonTag("entity")
                else:
                    ent = None
                if ent == entity:
                    # LOS is valid.
                    return (True, ent)
                else:
                    # LOS not established.  Blocked by another entity.
                    return (False, ent)

            # LOS is valid.
            return (True, None)

        def isPointVisible(self, point, traceMask):
            """
            Returns true if the indicated point if visible from the entity's
            eye position, or false if there is something in the way.
            """

            lookerOrigin = self.getEyePosition()
            dir = point - lookerOrigin
            dist = dir.length()
            dir.normalize()
            filter = PhysQueryNodeFilter(self, PhysQueryNodeFilter.FTExclude)
            result = PhysRayCastResult()
            base.physicsWorld.raycast(result, lookerOrigin, dir, dist, traceMask, 0, 0, filter)
            if result.hasBlock():
                block = result.getBlock()
                node = block.getActor()
                if node:
                    np = NodePath(node)
                    ent = np.getNetPythonTag("entity")
                else:
                    ent = None
                # LOS to point is blocked by this entity.
                return (False, ent)

            # LOS is valid.
            return (True, None)

        def onKillEntity(self, ent):
            pass

        def takeHealth(self, hp, bits):
            if self.takeDamageMode < TakeDamage.Yes:
                return 0

            if self.health >= self.maxHealth:
                return 0

            oldHealth = self.health
            self.health += hp
            if self.health > self.maxHealth:
                self.health = self.maxHealth

            return self.health - oldHealth

    else:

        # IS_CLIENT
        def emitSound_sv(self, soundIndex, waveIndex, volume, pitch, chan, loop):
            sound = Sounds.createSoundClient(soundIndex, waveIndex, volume, pitch)
            if sound is not None:
                self.soundEmitter.registerSound(sound,chan)
                sound.setLoop(bool(loop))
                sound.play()

        def emitSoundSpatial_sv(self, soundIndex, waveIndex, volume, pitch, chan, offset, loop):
            sound = Sounds.createSoundClient(soundIndex, waveIndex, volume, pitch, True)
            if sound is None:
                return

            self.soundEmitter.registerSound(sound,
                chan,
                True, offset)
            sound.setLoop(bool(loop))
            sound.play()

        def emitSound(self, soundName, loop=False, volume=None, chan=None):
            if isinstance(soundName, str):
                sound, info = Sounds.createSoundByName(soundName, getInfo=True)
            else:
                sound, info = Sounds.createSoundByIndex(soundName, getInfo=True)

            if sound is not None:
                if chan is None:
                    chan = info.channel
                self.soundEmitter.registerSound(sound, chan)
                if volume is not None:
                    sound.setVolume(volume)
                sound.setLoop(loop)
                sound.play()
            return sound

        def emitSoundSpatial(self, soundName, offset=(0, 0, 2), volume=None, loop=False, chan=None):
            if isinstance(soundName, str):
                sound, info = Sounds.createSoundByName(soundName, spatial=True, getInfo=True)
            else:
                sound, info = Sounds.createSoundByIndex(soundName, spatial=True, getInfo=True)

            if sound is None:
                return None
            if volume is not None:
                sound.setVolume(volume)
            sound.setLoop(loop)
            if chan is None:
                chan = info.channel
            self.soundEmitter.registerSound(sound,
                chan,
                True, offset)
            sound.play()
            return sound

        def getSpatialAudioCenter(self):
            # Returns the world-space center point for spatial audio
            # being emitted from this entity.  Spatial sounds can be
            # offset from this matrix.
            return self.getMat(base.render)

    def dispatchTraceAttack(self, info, dir, hit):
        # TODO: Damage filter?
        self.traceAttack(info, dir, hit)

    def traceAttack(self, info, dir, hit):
        if self.takeDamageMode:
            addMultiDamage(info, self)

            # TODO: Blood?

    def delete(self):
        if IS_CLIENT:
            self.ivPos = None
            self.ivRot = None
            self.ivScale = None
            self.shutdownPredictable()
            self.soundEmitter.delete()
            self.soundEmitter = None
        else:
            self.connMgr.cleanup()
            self.connMgr = None
            base.entMgr.removeEntity(self)
        # There's no point in replacing the physics node with a PandaNode
        # since we're about to delete it anyway.  Saves a tiny bit of time.
        self.destroyCollisions(replaceWithNormalNode=False)
        self.parentEntity = None
        #self.physicsRoot = None
        if not self.isEmpty():
            self.removeNode()
        BaseClass.delete(self)

if not IS_CLIENT:
    DistributedEntityAI = DistributedEntity
    DistributedEntityAI.__name__ = 'DistributedEntityAI'

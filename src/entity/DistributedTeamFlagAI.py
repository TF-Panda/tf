"""DistributedTeamFlagAI module: contains the DistributedTeamFlagAI class."""

from panda3d.pphysics import *
from panda3d.core import *

from tf.tfbase.TFGlobals import TFTeam, SpeechConcept, WorldParent, SolidShape, SolidFlag
from tf.tfbase import CollisionGroups, TFFilters
from tf.distributed.GameContextMessages import GameContextMessage

from .DistributedEntity import DistributedEntityAI

# TODO: Use the trigger from the map.
class CaptureZone:

    def __init__(self, team, pos):
        sphere = PhysSphere(128.0)
        shape = PhysShape(sphere, PhysMaterial(0, 0, 0))
        shape.setSimulationShape(False)
        shape.setTriggerShape(True)
        shape.setSceneQueryShape(False)
        node = PhysRigidStaticNode("capture-zone")
        node.addShape(shape)
        # This is what the trigger responds to.
        if team == TFTeam.Red:
            node.setIntoCollideMask(CollisionGroups.RedPlayer)
        else:
            node.setIntoCollideMask(CollisionGroups.BluePlayer)
        node.addToScene(base.physicsWorld)
        node.setTriggerCallback(CallbackObject.make(self.__triggerCallback))
        np = NodePath(node)
        np.setPos(pos)
        self.np = np
        self.team = team
        self.destroyed = False

    def destroy(self):
        self.np.node().removeFromScene(base.physicsWorld)
        self.np.removeNode()
        self.np = None
        self.team = None
        self.destroyed = True

    def __triggerCallback(self, cbdata):
        if self.destroyed:
            return

        node = cbdata.getOtherNode()
        entity = node.getPythonTag("entity")
        if not entity:
            return
        if not entity.isPlayer():
            return
        if entity.team != self.team:
            return
        if entity.isDead():
            return
        if cbdata.getTouchType() == PhysTriggerCallbackData.TEnter:
            if entity.flag:
                announce = not base.game.gameModeImpl.flagCaptured(self.team)
                base.game.sendUpdate('capturedFlagEvent', [entity.doId])
                entity.speakConcept(SpeechConcept.CappedObjective, {'gamemode': 'ctf'})
                if entity.flag:
                    entity.flag.returnFlag(True, announce)
                    entity.flag = None

class DistributedTeamFlagAI(DistributedEntityAI):

    def __init__(self):
        DistributedEntityAI.__init__(self)

        self.initialPos = Point3()
        self.initialHpr = Vec3()
        self.dropped = 0

        self.flagModelName = ""
        self.playerWithFlag = -1

        self.parentEntityId = WorldParent.DynRender

        # 32x32x32 trigger box for picking up the flag.
        self.solidShape = SolidShape.Box
        self.hullMins = Point3(-32)
        self.hullMaxs = Point3(32)
        self.solidFlags = SolidFlag.Trigger
        self.triggerCallback = True

    def initFromLevel(self, ent, properties):
        DistributedEntityAI.initFromLevel(self, ent, properties)

        # Save off the initial position and orientation for
        # when the flag gets returned.
        self.initialPos = self.getPos()
        self.initialHpr = self.getHpr()

        if not properties.hasAttribute("flag_model"):
            self.flagModelName = "models/flag/briefcase"
        else:
            self.flagModelName = Filename.fromOsSpecific(
                properties.getAttributeValue("flag_model").getString()).getFullpathWoExtension()

        #self.setFromCollideMask(CollisionGroups.Trigger)
        # Respond to trigger touches by players of the opposing team.
        if self.team == TFTeam.Red:
            self.setIntoCollideMask(CollisionGroups.BluePlayer)
        else:
            self.setIntoCollideMask(CollisionGroups.RedPlayer)

    def generate(self):
        DistributedEntityAI.generate(self)

        # Initialize the trigger box for pickups.
        self.initializeCollisions()

        self.capZone = CaptureZone(self.team, self.initialPos)

    def onEnemyTouch(self, player):
        if self.playerWithFlag != -1:
            return

        if not base.game.gameModeImpl.canPickupFlag():
            return

        self.removeTask('returnFlagTask')

        self.enemySound("CaptureFlag.TeamStolen")
        self.teamSound("CaptureFlag.EnemyStolen")

        base.game.d_setGameContextMessage(GameContextMessage.CTF_Enemy_PickedUp, 3, self.team, self.team)
        # We send a specific context message to the player that picked it up.
        base.game.d_setGameContextMessage(GameContextMessage.CTF_Team_PickedUp, 3, self.team, not self.team, exclude=[player])
        base.game.d_setGameContextMessage(GameContextMessage.CTF_Player_PickedUp, 3, self.team, forPlayer=player)

        base.game.sendUpdate('pickedUpFlagEvent', [player.doId])

        self.skin = self.team + 3

        self.dropped = 0

        self.playerWithFlag = player.doId
        player.flag = self

        # Parent the flag to the player.
        self.setParentEntityId(player.doId)
        # And zero out the transform.
        self.setPosHpr(0, 0, 0, 0, 0, 0)
        self.teleport()

    def onTriggerEnter(self, entity):
        if entity.isPlayer() and (entity.team != self.team) and not entity.isDead():
            # Player on other team touched us.
            self.onEnemyTouch(entity)

    def enemySound(self, snd):
        for plyr in base.game.playersByTeam[not self.team]:
            base.world.emitSound(snd, client=plyr.owner)

    def teamSound(self, snd):
        for plyr in base.game.playersByTeam[self.team]:
            base.world.emitSound(snd, client=plyr.owner)

    def defendedBy(self, player):
        base.game.sendUpdate('defendedFlagEvent', [player.doId])

    def drop(self):
        if self.playerWithFlag == -1:
            return

        self.enemySound("CaptureFlag.TeamDropped")
        self.teamSound("CaptureFlag.EnemyDropped")
        base.game.d_setGameContextMessage(GameContextMessage.CTF_Enemy_Dropped, 3, self.team, self.team)
        base.game.d_setGameContextMessage(GameContextMessage.CTF_Team_Dropped, 3, self.team, not self.team)

        self.setParentEntityId(WorldParent.DynRender)

        plyr = base.air.doId2do.get(self.playerWithFlag)
        assert plyr
        plyr.flag = None
        # Drop to ground underneath player.
        pos = plyr.getPos() + (0, 0, 32)
        tr = TFFilters.traceBox(pos, pos + Vec3.down() * 10000, Point3(-22.5, 12.75, -5.5), Point3(22.55, 13.34, 6.1),
                                CollisionGroups.World, TFFilters.TFQueryFilter(self), Vec3(plyr.getH(), 0, 0))
        if tr['hit']:
            self.setPos(tr['endpos'])
            self.setHpr(plyr.getH(), 0, 0)
            self.teleport()

        self.skin = self.team

        self.dropped = 1

        # Return flag after 60 seconds if no one picks it back up.
        self.addTask(self.__returnTask, 'returnFlagTask', delay=60.0, appendTask=True)

        self.playerWithFlag = -1

    def returnFlag(self, captured, announce=True):
        self.setParentEntityId(WorldParent.DynRender)
        self.setPos(self.initialPos)
        self.setHpr(self.initialHpr)
        self.teleport()
        self.skin = self.team
        if announce:
            if captured:
                # Flag was captured.
                self.enemySound("CaptureFlag.TeamCaptured")
                self.teamSound("CaptureFlag.EnemyCaptured")
                base.game.d_setGameContextMessage(GameContextMessage.CTF_Enemy_Captured, 3, self.team, self.team)
                base.game.d_setGameContextMessage(GameContextMessage.CTF_Team_Captured, 3, self.team, not self.team)
            else:
                self.enemySound("CaptureFlag.TeamReturned")
                self.teamSound("CaptureFlag.EnemyReturned")
                base.game.d_setGameContextMessage(GameContextMessage.CTF_Enemy_Returned, 3, self.team, not self.team)
                base.game.d_setGameContextMessage(GameContextMessage.CTF_Team_Returned, 3, self.team, self.team)
        if self.playerWithFlag != -1:
            plyr = base.air.doId2do.get(self.playerWithFlag)
            if plyr:
                plyr.flag = None
        self.playerWithFlag = -1
        self.dropped = 0
        self.removeTask('returnFlagTask')

    def __returnTask(self, task):
        self.returnFlag(False)
        return task.done

    def delete(self):
        self.capZone.destroy()
        del self.capZone
        DistributedEntityAI.delete(self)

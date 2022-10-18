from direct.distributed2.ServerRepository import ServerRepository

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.DistributedGameAI import DistributedGameAI
from tf.distributed.World import WorldAI
from tf.tfbase import TFGlobals

from tf.player.LagCompensation import LagCompensation

class TFServerRepository(ServerRepository):
    notify = directNotify.newCategory("TFServerRepository")

    def __init__(self, port):
        ServerRepository.__init__(self, port)

        self.readDCFiles()

        base.sv = self

        self.lagComp = LagCompensation()
        base.simTaskMgr.add(self.__recordPlayerPositions, 'recordPlayerPositions', sort=1000)

        self.game = DistributedGameAI()
        base.game = self.game
        self.generateObject(self.game, TFGlobals.UberZone)

    def syncAllHitBoxes(self):
        from tf.actor.DistributedCharAI import DistributedCharAI
        DistributedCharAI.syncAllHitBoxes()

    def __recordPlayerPositions(self, task):
        self.lagComp.recordPlayerPositions()
        return task.cont

    def addSnapshotHeaderData(self, dg, client):
        if not hasattr(client, 'player') or not client.player:
            dg.addUint32(0)
        else:
            # Acknowledge the most recently executed client command.
            dg.addUint32(client.player.lastRunCommandNumber)

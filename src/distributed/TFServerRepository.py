from direct.distributed2.ServerRepository import ServerRepository

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.DistributedGameAI import DistributedGameAI
from tf.distributed.World import WorldAI
from tf.tfbase import TFGlobals

class TFServerRepository(ServerRepository):
    notify = directNotify.newCategory("TFServerRepository")

    def __init__(self, port):
        ServerRepository.__init__(self, port)

        self.readDCFiles()

        base.sv = self

        self.game = DistributedGameAI()
        base.game = self.game
        self.generateObject(self.game, TFGlobals.UberZone)

        self.world = WorldAI()
        self.generateObject(self.world, TFGlobals.GameZone)

    def addSnapshotHeaderData(self, dg, client):
        if not hasattr(client, 'player') or not client.player:
            dg.addUint32(0)
        else:
            # Acknowledge the most recently executed client command.
            dg.addUint32(client.player.lastRunCommandNumber)

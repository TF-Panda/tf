from direct.distributed2.ServerRepository import ServerRepository

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.DistributedGameAI import DistributedGameAI
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

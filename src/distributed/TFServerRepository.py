from direct.distributed2.ServerRepository import ServerRepository

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.DistributedGameAI import DistributedGameAI
from tf.distributed.World import WorldAI
from tf.tfbase import TFGlobals

from tf.player.LagCompensation import LagCompensation

from panda3d.core import BitArray

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

    def sendUpdatePHSOnly(self, do, name, args, refPos, client=None, excludeClients=[]):
        if client:
            # This is targeted update, just send it to them.
            self.sendUpdate(do, name, args, client=client)
            return

        tree = self.game.lvlData.getAreaClusterTree()
        leaf = tree.getLeafValueFromPoint(refPos)
        if leaf == -1:
            return
        print("phs filter at pos", refPos)
        phs = BitArray()
        pvs = self.game.lvlData.getClusterPvs(leaf)
        for i in range(pvs.getNumHearableClusters()):
            phs.setBit(pvs.getHearableCluster(i))
        print("filter ref leaf", leaf)
        print(phs.getNumOnBits(), "hearable leaves")

        excludeClients = list(excludeClients)
        for cl in self.clientsByConnection.values():
            if cl in excludeClients:
                continue
            if not hasattr(cl, 'player'):
                continue
            if not cl.player:
                continue
            clLeaf = tree.getLeafValueFromPoint(cl.player.getEyePosition())
            if clLeaf == -1 or not phs.getBit(clLeaf):
                print(cl, "not in phs")
                excludeClients.append(cl)

        self.sendUpdate(do, name, args, excludeClients=excludeClients)

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

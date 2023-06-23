from direct.distributed2.ServerRepository import ServerRepository
from direct.distributed2.ServerRepository import ClientState
from direct.distributed2.NetMessages import NetMessages
from direct.distributed.PyDatagram import PyDatagram

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.distributed.DistributedGameAI import DistributedGameAI
from tf.distributed.TFMagicWordManagerAI import TFMagicWordManagerAI
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

        self.magicWordManager = TFMagicWordManagerAI()
        self.generateObject(self.magicWordManager, TFGlobals.MagicWordZone)

    def isValidClientInterest(self, zoneId):
        # The client can only request interest to the uber zone.
        return zoneId == TFGlobals.UberZone

    def wantAuthentication(self):
        return base.config.GetBool('tf-want-captcha', False)

    def sendClientAuthRequest(self, client):
        # Generate a Captcha for the client to answer.
        from captcha.image import ImageCaptcha
        import random
        from direct.distributed2.NetMessages import NetMessages

        img = ImageCaptcha()
        numChars = random.randint(4, 6)
        validChars = [
            'A', 'B', 'C', 'D', 'E', 'F',
            'G', 'H', 'I', 'J', 'K', 'L',
            'M', 'N', 'O', 'P', 'Q', 'R',
            'S', 'T', 'U', 'V', 'W', 'X',
            'Y', 'Z', '?', '!', '+', '#',
            '$', '%', '@', '&'
        ]
        chars = ""
        for i in range(numChars):
            chars += random.choice(validChars)
        client.authString = chars
        client.authAttemptsLeft = base.config.GetInt('tf-captcha-attempts', 4)
        data = img.generate(chars, 'jpeg')

        dg = PyDatagram()
        dg.addUint16(NetMessages.SV_AuthenticateRequest)
        dg.appendData(data.read())

        self.sendDatagram(dg, client.connection)

    def handleClientAuthResponse(self, client, dgi):
        answer = dgi.getString()
        if answer == client.authString:
            # Good to go.
            client.state = ClientState.Verified
            client.id = self.clientIdAllocator.allocate()

            self.notify.info("Client %i authenticated, given ID %i" % (client.connection, client.id))
            self.notify.info("Client lerp time: " + str(client.interpAmount))

            dg = PyDatagram()
            dg.addUint16(NetMessages.SV_AuthenticateResponse)
            dg.addBool(True)
            # Tell the client their ID and our tick rate.
            dg.addUint16(client.id)
            dg.addUint8(base.ticksPerSec)
            dg.addUint32(base.tickCount)

            self.numClients += 1

            self.sendDatagram(dg, client.connection)

            messenger.send('clientConnected', [client])
        else:
            client.authAttemptsLeft -= 1
            if client.authAttemptsLeft <= 0:
                self.notify.info("Client %i failed to complete auth, dropping." % client.connection)
                self.closeClientConnection(client)
            else:
                self.notify.info("Client %i failed auth, %i attempts left." % (client.connection, client.authAttemptsLeft))
                dg = PyDatagram()
                dg.addUint16(NetMessages.SV_AuthenticateResponse)
                dg.addBool(False)
                dg.addUint8(client.authAttemptsLeft)
                self.sendDatagram(dg, client.connection)

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

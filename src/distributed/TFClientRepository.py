from direct.distributed2.ClientRepository import ClientRepository
from direct.fsm.FSM import FSM
from direct.gui.DirectGui import DirectDialog, RetryCancelDialog, OkCancelDialog

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.tfbase import TFLocalizer
from tf.tfbase import TFGlobals

class TFClientRepository(ClientRepository, FSM):
    notify = directNotify.newCategory("TFClientRepository")

    def __init__(self, info):
        ClientRepository.__init__(self)
        FSM.__init__(self, "TFClientRepository")
        self.readDCFiles()

        self.connectInfo = None

        self.accept('connectionLost', self.handleConnectionLost)

        self.request("Connect", info)

    def shutdown(self):
        self.disconnect()
        self.ignoreAll()
        self.connectInfo = None
        self.request("Off")

    def handleConnectionLost(self):
        self.request("ConnectionLost")

    def enterConnect(self, info):
        self.connectInfo = info
        self.acceptOnce('connectSuccess', self.handleConnectSuccess)
        self.acceptOnce('connectFailure', self.handleConnectFailure)
        self.connectDialog = DirectDialog(text = TFLocalizer.ConnectingToServer % str(info['addr']))
        self.connect(info['addr'])

    def handleConnectSuccess(self, addr):
        self.request("Authenticate")

    def handleConnectFailure(self, addr):
        self.request("ConnectionFailed")

    def exitConnect(self):
        self.ignore('connectSuccess')
        self.ignore('connectFailure')
        self.connectDialog.cleanup()
        del self.connectDialog

    def enterConnectionFailed(self):
        self.dialog = RetryCancelDialog(text = TFLocalizer.ConnectionFailed % self.connectInfo['addr'],
                                        command = self.__connectionFailedAck,
                                        buttonTextList = [TFLocalizer.Retry, TFLocalizer.Cancel])

    def __connectionFailedAck(self, value):
        if value > 0:
            self.request("Connect", self.connectInfo)
        else:
            base.request("MainMenu")

    def exitConnectionFailed(self):
        self.dialog.cleanup()
        del self.dialog

    def enterAuthenticate(self):
        self.dialog = DirectDialog(text = TFLocalizer.Authenticating)
        self.dialog.show()
        self.sendHello()
        self.acceptOnce('serverHelloSuccess', self.handleHelloSuccess)
        self.acceptOnce('serverHelloFail', self.handleHelloFail)

    def handleHelloSuccess(self):
        self.request("JoinGame")

    def handleHelloFail(self, msg):
        self.notify.warning("Server hello failed: %s" % msg)
        base.request("MainMenu")

    def exitAuthenticate(self):
        self.dialog.cleanup()
        del self.dialog
        self.ignore('serverHelloSuccess')
        self.ignore('serverHelloFail')

    def enterJoinGame(self):
        self.dialog = DirectDialog(text = TFLocalizer.JoiningGame)
        self.dialog.show()
        # Enter the uber zone to start talking to the game manager.
        self.handle = self.addInterest([TFGlobals.UberZone])
        self.accept('interestComplete', self.__onUberInterestComplete)

    def __onUberInterestComplete(self, handle):
        if handle != self.handle:
            return

        self.request("InGame")

    def exitJoinGame(self):
        self.ignore('interestComplete')
        self.dialog.cleanup()
        del self.dialog

    def enterInGame(self):
        pass

    def exitInGame(self):
        pass

    def enterConnectionLost(self):
        self.dialog = OkCancelDialog(text = TFLocalizer.LostConnection,
                                     buttonTextList = [TFLocalizer.OK, TFLocalizer.Cancel],
                                     command = self.__onLostConnectionAck)
        self.dialog.show()

    def __onLostConnectionAck(self, value):
        if value > 0:
            self.request("Connect", self.connectInfo)
        else:
            base.request("MainMenu")

    def exitConnectionLost(self):
        self.dialog.cleanup()
        del self.dialog



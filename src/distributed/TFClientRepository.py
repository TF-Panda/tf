from direct.distributed2.ClientRepository import ClientRepository
from direct.fsm.FSM import FSM
from direct.gui.DirectGui import DirectDialog, RetryCancelDialog, OkCancelDialog, OkDialog
from direct.gui import DirectGuiGlobals as DGG

from tf.tfgui.TFDialog import TFDialog

from direct.directnotify.DirectNotifyGlobal import directNotify

from tf.player.Prediction import Prediction

from tf.tfbase import TFLocalizer
from tf.tfbase import TFGlobals

class TFClientRepository(ClientRepository, FSM):
    notify = directNotify.newCategory("TFClientRepository")

    def __init__(self, info):
        ClientRepository.__init__(self)
        FSM.__init__(self, "TFClientRepository")
        self.readDCFiles()

        self.prediction = Prediction()

        self.connectInfo = None

        self.accept('connectionLost', self.handleConnectionLost)

        self.loadingMusic = base.loader.loadMusic("misc/training_vid_ctf_2fort.mp3")
        self.loadingMusic.play()
        #base.musicManager.update()

        self.request("Connect", info)

    def syncAllHitBoxes(self):
        from tf.actor.DistributedChar import DistributedChar
        DistributedChar.syncAllHitBoxes()

    def runPrediction(self):
        if not self.connected or not hasattr(base, 'localAvatar'):
            return

        if self.deltaTick < 0:
            # No valid snapshot received yet.
            return

        valid = self.deltaTick > 0
        # Predict the player's actions.
        self.prediction.update(self.deltaTick, valid, base.localAvatar.lastCommandAck,
                               base.localAvatar.lastOutgoingCommand + base.localAvatar.chokedCommands)

    def readSnapshotHeaderData(self, dgi):
        # What's the latest command number that the server ran?
        commandAck = dgi.getUint32()
        if hasattr(base, 'localAvatar') and base.localAvatar is not None:
            base.localAvatar.commandAck = commandAck

    def postSnapshot(self):
        if not hasattr(base, 'localAvatar'):
            return
        commandsAcked = base.localAvatar.commandAck - base.localAvatar.lastCommandAck
        base.localAvatar.lastCommandAck = base.localAvatar.commandAck
        self.prediction.postNetworkDataReceived(commandsAcked)

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
        self.connectDialog = TFDialog(style = TFDialog.NoButtons, text = TFLocalizer.ConnectingToServer % str(info['addr']))
        self.connectDialog.show()
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
        self.dialog = TFDialog(style = TFDialog.OkCancel, text = TFLocalizer.ConnectionFailed % self.connectInfo['addr'],
                               command = self.__connectionFailedAck)
        self.dialog.show()

    def __connectionFailedAck(self, value):
        if value > 0:
            self.request("Connect", self.connectInfo)
        else:
            base.request("MainMenu")

    def exitConnectionFailed(self):
        self.dialog.cleanup()
        del self.dialog

    def enterAuthenticate(self):
        self.dialog = TFDialog(style = TFDialog.NoButtons, text = TFLocalizer.Authenticating)
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
        self.dialog = TFDialog(style = TFDialog.NoButtons, text = TFLocalizer.JoiningGame)
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
        self.loadingMusic.stop()
        # Interpolation is sort 30, so make sure prediction happens before interpolation.
        base.taskMgr.add(self.runPredictionTask, 'runPredictionTask', sort = 29)

    def runPredictionTask(self, task):
        self.runPrediction()
        return task.cont

    def exitInGame(self):
        base.taskMgr.remove('runPredictionTask')

    def enterConnectionLost(self):
        self.dialog = TFDialog(style = TFDialog.Acknowledge, text = TFLocalizer.LostConnection,
                               command = self.__onLostConnectionAck,
                               text_wordwrap = 18)
        self.dialog.show()

    def __onLostConnectionAck(self, value):
        base.request("MainMenu")

    def exitConnectionLost(self):
        self.dialog.cleanup()
        del self.dialog



"""DistributedTeamFlag module: contains the DistributedTeamFlag class."""

from direct.interval.IntervalGlobal import LerpHprInterval
from tf.actor.Model import Model
from tf.entity.DistributedEntity import DistributedEntity
from tf.player.DistributedTFPlayer import DistributedTFPlayer
from tf.tfbase import TFGlobals


class DistributedTeamFlag(DistributedEntity):
    """
    Flag entity for the CTF game mode.
    """

    def __init__(self):
        DistributedEntity.__init__(self)

        self.flagModelName = ""
        self.flagModel = None
        self.spinIval = None
        self.playerWithFlag = -1

    def parentChanged(self):
        if self.parentEntity and isinstance(self.parentEntity, DistributedTFPlayer):
            # Flag is carried by a player, actually parent the flag to the
            # "flag" expose joint.
            flagNode = self.parentEntity.find("**/flag")
            if not flagNode.isEmpty():
                self.reparentTo(flagNode)

    def RecvProxy_playerWithFlag(self, plyr):
        self.playerWithFlag = plyr
        if plyr == -1:
            self.startSpin()
        else:
            self.stopSpin()

    def setFlagModel(self, model):
        self.flagModelName = model

        if self.flagModel:
            self.flagModel.cleanup()
            self.flagModel = None
        self.flagModel = Model()
        # Set to color of team.
        self.flagModel.setSkin(TFGlobals.getTeamSkin(self.team))
        self.flagModel.loadModel(model)
        self.flagModel.modelNp.reparentTo(self)

    def startSpin(self):
        self.stopSpin()

        if self.flagModel and self.flagModel.modelNp:
            self.spinIval = LerpHprInterval(self.flagModel.modelNp, 3.0, (360, 0, 0), (0, 0, 0))
            self.spinIval.loop()

    def stopSpin(self):
        if self.spinIval:
            self.spinIval.finish()
            self.spinIval = None

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        self.setFlagModel(self.flagModelName)
        self.startSpin()

    def disable(self):
        self.stopSpin()
        if self.flagModel:
            self.flagModel.cleanup()
            self.flagModel = None
        DistributedEntity.disable(self)

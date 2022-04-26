"""DistributedTeamFlag module: contains the DistributedTeamFlag class."""

from panda3d.core import *

from direct.interval.IntervalGlobal import LerpHprInterval

from tf.tfbase.TFGlobals import Contents, SolidShape, SolidFlag

from tf.entity.DistributedEntity import DistributedEntity

class DistributedTeamFlag(DistributedEntity):
    """
    Flag entity for the CTF game mode.
    """

    def __init__(self):
        DistributedEntity.__init__(self)

        self.initialPos = Point3()
        self.initialHpr = Vec3()
        self.flagModelName = ""
        self.flagModel = None
        self.spinIval = None

        # 32x32x32 trigger box for picking up the flag.
        self.solidShape = SolidShape.Box
        self.hullMins = Point3(-32)
        self.hullMaxs = Point3(32)
        self.solidFlags = SolidFlag.Trigger
        self.triggerCallback = True

    if not IS_CLIENT:

        def initFromLevel(self, properties):
            DistributedEntity.initFromLevel(self, properties)

            # Save off the initial position and orientation for
            # when the flag gets returned.
            self.initialPos = self.getPos()
            self.initialHpr = self.getHpr()

            self.flagModelName = properties.getAttributeValue("flag_model").getString()

            self.team = properties.getAttributeValue("TeamNum").getInt() - 2

            if self.team == 0:
                self.setContentsMask(Contents.RedTeam)
                self.setSolidMask(Contents.BlueTeam)
            else:
                self.setContentsMask(Content.BlueTeam)
                self.setSolidMask(Contents.RedTeam)

        def generate(self):
            DistributedEntity.generate(self)

            # Initialize the trigger box for pickups.
            self.initializeCollisions()

        def onEnemyTouch(self, player):
            print(player, "touched flag")

        def onTriggerEnter(self, entity):
            from tf.player.DistributedTFPlayerAI import DistributedTFPlayerAI
            if entity.isPlayer() and entity.team != self.team:
                # Player on other team touched us.
                self.onEnemyTouch(entity)

    else: # IS_CLIENT

        def setFlagModel(self, model):
            self.flagModelName = model

            if self.flagModel:
                self.flagModel.removeNode()
                self.flagModel = None
            self.flagModel = base.loader.loadModel(model)
            # Set to color of team.
            self.flagModel.node().setActiveMaterialGroup(self.team)
            self.flagModel.reparentTo(self)

        def startSpin(self):
            self.stopSpin()

            self.spinIval = LerpHprInterval(self.flagModel, 3.0, (360, 0, 0), (0, 0, 0))
            self.spinIval.loop()

        def stopSpin(self):
            if self.spinIval:
                self.spinIval.finish()
                self.spinIval = None

        def announceGenerate(self):
            DistributedEntity.announceGenerate(self)
            self.reparentTo(base.dynRender)
            self.setFlagModel(self.flagModelName)
            self.startSpin()

        def disable(self):
            self.stopSpin()
            if self.flagModel:
                self.flagModel.removeNode()
                self.flagModel = None
            DistributedEntity.disable(self)

if not IS_CLIENT:
    DistributedTeamFlagAI = DistributedTeamFlag
    DistributedTeamFlagAI.__name__ = 'DistributedTeamFlagAI'

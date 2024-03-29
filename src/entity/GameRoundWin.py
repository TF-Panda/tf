"""GameRoundWin module: contains the GameRoundWin class."""

from tf.tfbase import TFGlobals

from .EntityBase import EntityBase


class GameRoundWin(EntityBase):

    def __init__(self):
        EntityBase.__init__(self)
        self.team = TFGlobals.TFTeam.NoTeam
        self.switchTeams = False
        self.forceMapReset = False

    def initFromLevel(self, ent, props):
        EntityBase.initFromLevel(self, ent, props)
        if props.hasAttribute("TeamNum"):
            self.team = props.getAttributeValue("TeamNum").getInt()
        if props.hasAttribute("switch_teams"):
            self.switchTeams = props.getAttributeValue("switch_teams").getBool()
        if props.hasAttribute("force_map_reset"):
            self.forceMapReset = props.getAttributeValue("force_map_reset").getBool()

    def input_RoundWin(self, caller):
        base.game.endRound(self.team, TFGlobals.WinReason.Defended)
        base.game.switchTeamsOnNewRound = self.switchTeams
        base.game.forceMapReset = self.forceMapReset

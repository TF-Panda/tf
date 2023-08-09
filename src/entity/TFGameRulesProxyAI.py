"""TFGameRulesProxyAI module: contains the TFGameRulesProxyAI class."""

from tf.tfbase import TFGlobals

from .EntityBase import EntityBase


class TFGameRulesProxyAI(EntityBase):

    def input_SetRedTeamGoalString(self, caller, string):
        base.game.setTeamGoalString(TFGlobals.TFTeam.Red, string)

    def input_SetBlueTeamGoalString(self, caller, string):
        base.game.setTeamGoalString(TFGlobals.TFTeam.Blue, string)

    def input_SetRedTeamRespawnWaveTime(self, caller, time):
        base.game.setTeamRespawnWaveTime(TFGlobals.TFTeam.Red, float(time))

    def input_setredteamrespawnwavetime(self, caller, time):
        base.game.setTeamRespawnWaveTime(TFGlobals.TFTeam.Red, float(time))

    def input_SetBlueTeamRespawnWaveTime(self, caller, time):
        base.game.setTeamRespawnWaveTime(TFGlobals.TFTeam.Blue, float(time))

    def input_setblueteamrespawnwavetime(self, caller, time):
        base.game.setTeamRespawnWaveTime(TFGlobals.TFTeam.Blue, float(time))

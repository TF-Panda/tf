"""DistributedFuncRespawnRoomAI module: contains the DistributedFuncRespawnRoomAI class."""


from tf.tfbase import TFGlobals

from .DistributedTrigger import DistributedTriggerAI


class DistributedFuncRespawnRoomAI(DistributedTriggerAI):

    def input_SetTeam(self, caller, team):
        if team != self.team:
            self.team = int(team)

            # Clear out all current players in spawn room.
            for ent in self.touching:
                if not ent.isDODeleted() and ent.isPlayer() and not self.isValidForPlayer(ent):
                    ent.clearRespawnRoom(self.doId)

    def isValidForPlayer(self, player):
        """
        Returns true if the respawn room has an effect on this player.
        """
        return self.team == TFGlobals.TFTeam.NoTeam or player.team == self.team

    def onEntityStartTouch(self, entity):
        DistributedTriggerAI.onEntityStartTouch(self, entity)
        if entity.isPlayer() and self.isValidForPlayer(entity):
            entity.addRespawnRoom(self.doId)

    def onEntityEndTouch(self, entity):
        DistributedTriggerAI.onEntityEndTouch(self, entity)
        if entity.isPlayer():
            entity.clearRespawnRoom(self.doId)

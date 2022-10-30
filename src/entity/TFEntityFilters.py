"""TFEntityFilters module: contains the TFEntityFilters class."""

from .FilterBase import FilterBase

from tf.tfbase import TFGlobals

class FilterActivatorTFTeam(FilterBase):

    def __init__(self):
        FilterBase.__init__(self)
        self.teamNum = TFGlobals.TFTeam.NoTeam

    def initFromLevel(self, ent, props):
        FilterBase.initFromLevel(self, ent, props)
        if props.hasAttribute("TeamNum"):
            self.teamNum = props.getAttributeValue("TeamNum").getInt() - 2

    def doFilter(self, activator):
        if not activator.isPlayer():
            return False

        print("test", activator, "against filter_activator_tfteam")
        print(activator.team, self.teamNum)

        if base.game.isRoundEnded() and not base.game.isStalemate():
            # If it's not a stalemate, we allow the winning team and the
            # set team.
            print("in non-stalemate round end, allowing win team as well")
            return activator.team in (self.teamNum, base.game.winTeam)
        # Otherwise, we only allow the set team.
        return activator.team == self.teamNum

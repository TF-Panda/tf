"""TeamControlPointManagerAI module: contains the TeamControlPointManagerAI class."""

from tf.tfbase import TFGlobals

from .EntityBase import EntityBase


class TeamControlPointManagerAI(EntityBase):
    """
    This is a base class between TeamControlPointMasterAI and TeamControlPointRoundAI.
    It manages a group of control points.
    """

    # Defines how to limit which teams can win the control point
    # group.
    RestrictNeither = 0
    RestrictBoth = 1
    RestrictRed = 2
    RestrictBlue = 3

    def __init__(self):
        EntityBase.__init__(self)
        self.points = []
        self.restrictWinTeam = self.RestrictNeither

    def getPointByIndex(self, index):
        for p in self.points:
            if p.pointIndex == index:
                return p
        return None

    def canTeamWin(self, team):
        """
        Returns True if the indicated team is allowed to win by capturing
        all control points.
        """

        if team is None:
            return False

        if self.restrictWinTeam == self.RestrictBoth:
            return False
        elif self.restrictWinTeam == self.RestrictNeither:
            return True
        elif self.restrictWinTeam == self.RestrictBlue:
            return team != TFGlobals.TFTeam.Blue
        elif self.restrictWinTeam == self.RestrictRed:
            return team != TFGlobals.TFTeam.Red

        return True

    def delete(self):
        self.points = None
        EntityBase.delete(self)

    def areAllPointsIdle(self):
        """
        Returns False if any points have partial capture progress, or
        True if they are all idle (no progress or full progress).
        """
        for p in self.points:
            if p.capProgress > 0 and p.capProgress < 1:
                return False
        return True

    def checkWinner(self):
        """
        Based on the current conditions of all control points within
        this group, returns the team number that should win, or None if
        nobody has won yet.
        """

        if self.restrictWinTeam == self.RestrictBoth:
            # No team can win this group... don't know why
            # this exists.
            return None

        # Determine the team that owns all control points.
        # If there is a team that owns them all, they should win,
        # but only if they are not restricted from winning.

        winTeam = None
        for p in self.points:
            if winTeam is None:
                winTeam = p.ownerTeam
            elif winTeam != p.ownerTeam:
                # Another team owns the point, so they aren't all won
                # by a single team.  Nobody wins yet.
                winTeam = None
                break

        if not self.canTeamWin(winTeam):
            return None

        if winTeam == TFGlobals.TFTeam.Red:
            self.connMgr.fireOutput("OnWonByTeam1")
        elif winTeam == TFGlobals.TFTeam.Blue:
            self.connMgr.fireOutput("OnWonByTeam2")

        # This team wins.
        return winTeam


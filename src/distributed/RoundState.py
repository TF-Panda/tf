"""RoundState module: contains the RoundState class."""

class RoundState:
    PreRound = 0
    # Pre-round start, set up time for defending team, etc.
    Setup = 1
    # Game in action.
    Playing = 2
    # Team has won or time ran out, loser state/win state.
    Ended = 3

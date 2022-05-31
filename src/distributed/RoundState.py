"""RoundState module: contains the RoundState class."""

class RoundState:
    # Pre-round start, set up time for defending team, etc.
    Setup = 0
    # Game in action.
    Playing = 1
    # Team has one or time ran out, loser state/win state.
    Ended = 2

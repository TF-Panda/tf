"""TFPlayerState module: contains the TFPlayerState class."""



class TFPlayerState:
    """
    Top-level TF player state.
    """

    # The player just joined the game and needs to pick a team and class.
    Fresh = 0

    # The player is in the world, alive and playing.
    Playing = 1

    # The player was killed and is doing the death cam.
    Died = 2

    # Spectating the game because they are waiting to respawn or are on
    # the spectator team.
    Spectating = 3

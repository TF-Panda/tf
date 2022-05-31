"""GameMode module: contains the GameMode class."""

class GameMode:
    Arena = 0
    CTF = 1
    ControlPoint = 2
    AttackDefend = 3
    Payload = 4

MapPrefixToGameMode = {
    'arena': GameMode.Arena,
    'ctf': GameMode.CTF,
    'cp': GameMode.ControlPoint,
    'ad': GameMode.AttackDefend,
    'pl': GameMode.Payload
}

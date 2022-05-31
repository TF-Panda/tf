
class ObjectState:
    Off = 0
    Constructing = 1
    Active = 2 # Built and running.
    Upgrading = 3 # Upgrading to next level.
    Disabled = 4 # Sapper attached, etc.

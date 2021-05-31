
from enum import IntFlag

class InputFlag(IntFlag):

    Empty         = 0
    MoveForward   = 1 << 0
    MoveBackward  = 1 << 1
    MoveLeft      = 1 << 2
    MoveRight     = 1 << 3
    Jump          = 1 << 4
    Crouch        = 1 << 5
    Run           = 1 << 6
    Walk          = 1 << 7
    Attack1       = 1 << 8
    Attack2       = 1 << 9
    Reload        = 1 << 10
    Taunt         = 1 << 11
    AxisX         = 1 << 12
    AxisY         = 1 << 13

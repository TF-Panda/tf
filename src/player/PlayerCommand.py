"""
PlayerCommand module: contains the PlayerCommand class

This class contains the inputs of a player for a particular server tick.  The
server runs the commands and the client predicts his own commands.
"""

from panda3d.core import Vec3, Vec2

from .InputButtons import InputFlag

import random

class PlayerCommand:

    def __init__(self, init=True):
        if init:
            self.clear()

    def makeCopy(self):
        p = PlayerCommand(False)
        p.buttons = self.buttons
        p.viewAngles = Vec3(self.viewAngles)
        p.mouseDelta = Vec2(self.mouseDelta)
        p.move = Vec3(self.move)
        p.weaponSelect = self.weaponSelect
        p.hasBeenPredicted = self.hasBeenPredicted
        p.tickCount = self.tickCount
        p.commandNumber = self.commandNumber
        p.randomSeed = self.randomSeed
        return p

    def clear(self):
        # Gameplay button states
        self.buttons = InputFlag.Empty

        # Player view angles
        self.viewAngles = Vec3()

        self.mouseDelta = Vec2()

        self.move = Vec3()

        self.weaponSelect = -1

        self.hasBeenPredicted = False

        self.tickCount = 0
        self.commandNumber = 0
        self.randomSeed = 0

    @staticmethod
    def readDatagram(dgi, prev):
        # Assume no change.
        cmd = prev.makeCopy()

        if dgi.getUint8():
            cmd.commandNumber = dgi.getUint32()
        else:
            # Assume steady increment.
            cmd.commandNumber = prev.commandNumber + 1

        rand = random.Random(cmd.commandNumber)
        cmd.randomSeed = rand.randint(0, 0xFFFFFFFF)

        if dgi.getUint8():
            cmd.tickCount = dgi.getUint32()
        else:
            # Assume steady increment.
            cmd.tickCount = prev.tickCount + 1

        if dgi.getUint8():
            cmd.viewAngles.readDatagramFixed(dgi)

        if dgi.getUint8():
            cmd.move.readDatagramFixed(dgi)

        if dgi.getUint8():
            cmd.buttons = dgi.getUint32()

        if dgi.getUint8():
            cmd.weaponSelect = dgi.getInt8()

        if dgi.getUint8():
            cmd.mouseDelta.readDatagramFixed(dgi)

        return cmd

    def writeDatagram(self, dg, prev):
        if self.commandNumber != (prev.commandNumber + 1):
            dg.addUint8(1)
            dg.addUint32(self.commandNumber)
        else:
            dg.addUint8(0)

        if self.tickCount != (prev.tickCount + 1):
            dg.addUint8(1)
            dg.addUint32(self.tickCount)
        else:
            dg.addUint8(0)

        if self.viewAngles != prev.viewAngles:
            dg.addUint8(1)
            self.viewAngles.writeDatagramFixed(dg)
        else:
            dg.addUint8(0)

        if self.move != prev.move:
            dg.addUint8(1)
            self.move.writeDatagramFixed(dg)
        else:
            dg.addUint8(0)

        if self.buttons != prev.buttons:
            dg.addUint8(1)
            dg.addUint32(self.buttons)
        else:
            dg.addUint8(0)

        if self.weaponSelect != prev.weaponSelect:
            dg.addUint8(1)
            dg.addInt8(self.weaponSelect)
        else:
            dg.addUint8(0)

        if self.mouseDelta != prev.mouseDelta:
            dg.addUint8(1)
            self.mouseDelta.writeDatagramFixed(dg)
        else:
            dg.addUint8(0)



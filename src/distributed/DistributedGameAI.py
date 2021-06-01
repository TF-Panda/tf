
from direct.distributed2.DistributedObjectAI import DistributedObjectAI

from tf.player.DistributedTFPlayerAI import DistributedTFPlayerAI
from tf.player.DViewModelAI import DViewModelAI

from tf.tfbase import TFGlobals, Sounds
from tf.player.TFClass import *
from .DTestCharAI import DTestCharAI
from tf.weapon.DShotgunAI import DShotgunAI
from tf.weapon.DWrenchAI import DWrenchAI

import random

from panda3d.core import Vec3

class DistributedGameAI(DistributedObjectAI):

    def __init__(self):
        DistributedObjectAI.__init__(self)
        self.numBlue = 0
        self.numRed = 0

    def d_emitSound(self, soundName, origin):
        #print("d_emitSound", soundName, origin)
        soundInfo = Sounds.createSoundServer(soundName, origin)
        #print(soundInfo)
        if soundInfo == None:
            return

        self.sendUpdate('emitSound', soundInfo)

    def playerCanTakeDamage(self, player, inflictor):
        print(player.__class__, inflictor.__class__, player, inflictor)
        return player.getTeam() != inflictor.getTeam()

    def allowDamage(self, player, inflictor):
        return player.getTeam() != inflictor.getTeam()

    def joinGame(self, name):
        print("Player " + name + " has joined the game.")

        client = base.sv.clientSender
        player = DistributedTFPlayerAI()
        player.name = name
        if self.numRed > self.numBlue:
            # Blue team
            player.team = 1
            self.numBlue += 1
        else:
            # Red team
            player.team = 0
            self.numRed += 1
        player.skin = player.team
        player.changeClass(Class.Engineer)
        player.setPos(Vec3(random.uniform(-64, 64), random.uniform(-64, 64), 0))
        player.setHpr(Vec3(random.uniform(-180, 180), 0, 0))
        base.sv.generateObject(player, TFGlobals.GameZone, client)

        # And a shotgun
        shotgun = DShotgunAI()
        shotgun.setPlayerId(player.doId)
        base.sv.generateObject(shotgun, player.zoneId)

        #wrench = DWrenchAI()
        #wrench.setPlayerId(player.doId)
        #base.sv.generateObject(wrench, player.zoneId)

        player.giveWeapon(shotgun.doId)
        #player.giveWeapon(wrench.doId)

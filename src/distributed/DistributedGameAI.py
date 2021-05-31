
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

    def d_emitSound(self, soundName, origin):
        #print("d_emitSound", soundName, origin)
        soundInfo = Sounds.createSoundServer(soundName, origin)
        #print(soundInfo)
        if soundInfo == None:
            return

        self.sendUpdate('emitSound', soundInfo)

    def joinGame(self, name):
        print("Player " + name + " has joined the game.")

        client = base.sv.clientSender
        player = DistributedTFPlayerAI()
        player.name = name
        player.changeClass(Class.Engineer)
        player.setPos(Vec3(random.uniform(-64, 64), random.uniform(-64, 64), 0))
        player.setHpr(Vec3(random.uniform(-180, 180), 0, 0))
        base.sv.generateObject(player, TFGlobals.GameZone, client)

        # And a shotgun
        shotgun = DShotgunAI()
        shotgun.setPlayerId(player.doId)
        base.sv.generateObject(shotgun, player.zoneId)

        wrench = DWrenchAI()
        wrench.setPlayerId(player.doId)
        base.sv.generateObject(wrench, player.zoneId)

        player.giveWeapon(shotgun.doId)
        player.giveWeapon(wrench.doId)

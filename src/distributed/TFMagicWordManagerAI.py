"""TFMagicWordManagerAI module: contains the TFMagicWordManagerAI class."""

from direct.distributed2.DistributedObjectAI import DistributedObjectAI

class TFMagicWordManagerAI(DistributedObjectAI):

    def __init__(self):
        DistributedObjectAI.__init__(self)

        self.magicWords = {
            "bot": self.__makeBot,
            "clearbots": self.__clearBots,
            "noclip": self.__toggleNoClip,
            "kill": self.__kill,
            "explode": self.__explode
        }

    def __makeBot(self, args, av):
        count = 1
        if len(args) > 0:
            count = int(args[0])
        for _ in range(count):
            base.game.makeBot('')
        return "Made " + str(count) + " bots"

    def __clearBots(self, args, av):
        base.game.clearBots()
        return "Bots cleared"

    def __toggleNoClip(self, args, av):
        from tf.movement.MoveType import MoveType
        av.toggleNoClip()
        if av.moveType == MoveType.NoClip:
            return "No clip ON"
        else:
            return "No clip OFF"

    def __kill(self, args, av):
        from tf.weapon.TakeDamageInfo import TakeDamageInfo
        from tf.tfbase.TFGlobals import DamageType
        info = TakeDamageInfo()
        info.damageType = DamageType.Generic
        info.inflictor = av
        info.attacker = av
        info.setDamage(100000)
        av.takeDamage(info)

    def __explode(self, args, av):
        from tf.weapon.TakeDamageInfo import TakeDamageInfo
        from tf.tfbase.TFGlobals import DamageType
        info = TakeDamageInfo()
        info.damageType = DamageType.Blast
        info.inflictor = av
        info.attacker = av
        info.setDamage(100000)
        av.takeDamage(info)

    def sendResponse(self, client, resp):
        self.sendUpdate('magicWordResp', [resp], client)

    def setMagicWord(self, cmd, args):
        client = base.air.clientSender
        if not client or not hasattr(client, 'player') or not client.player:
            return

        av = client.player

        if cmd in self.magicWords:
            try:
                resp = self.magicWords[cmd](args, av)
                if resp:
                    self.sendResponse(client, resp)
            except Exception as e:
                self.sendResponse(client, "Exception thrown in " + cmd + ": " + str(e))
        else:
            self.sendResponse(client, "Unknown magic word: " + cmd)



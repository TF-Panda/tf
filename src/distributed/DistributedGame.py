""" DistributedGame module: contains the DistributedGame class """

from direct.distributed2.DistributedObject import DistributedObject
from direct.directbase import DirectRender

from panda3d.core import *
from panda3d.pphysics import *

from direct.interval.IntervalGlobal import Sequence, Wait, Func

from tf.tfbase import Sounds

from .DistributedGameBase import DistributedGameBase

play_sound_coll = PStatCollector("App:Sounds:PlaySound")

class DistributedGame(DistributedObject, DistributedGameBase):

    def __init__(self):
        DistributedObject.__init__(self)
        DistributedGameBase.__init__(self)

    def worldLoaded(self):
        """
        Called by the world when its DO has been generated.  We can now load
        the level and notify the server we have joined the game.
        """
        self.changeLevel(self.levelName)
        self.sendUpdate("joinGame", ['Brian'])

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        base.game = self

    def changeLevel(self, lvlName):
        DistributedGameBase.changeLevel(self, lvlName)

        mrender = MapRender("mrender")
        mrender.replaceNode(base.render.node())
        mrender.setMapData(self.lvlData)

        vmrender = MapRender("vmrender")
        vmrender.replaceNode(base.vmRender.node())
        vmrender.setMapData(self.lvlData)

        render.setAttrib(LightRampAttrib.makeHdr0())

    def delete(self):
        del base.game
        DistributedObject.delete(self)
        DistributedGameBase.delete(self)

    def emitSound(self, soundIndex, waveIndex, volume, pitch, origin):
        sound = Sounds.createSoundClient(soundIndex, waveIndex, volume, pitch, origin)
        if sound:
            play_sound_coll.start()
            sound.play()
            play_sound_coll.stop()

    def doExplosion(self, pos, scale):
        root = base.render.attachNewNode("expl")
        root.setPos(Vec3(*pos))
        root.setScale(Vec3(*scale))
        expl = base.loader.loadModel("models/effects/explosion")
        expl.setZ(8)
        expl.hide(DirectRender.ShadowCameraBitmask)
        seqn = expl.find("**/+SequenceNode").node()
        seqn.play()
        expl.reparentTo(root)
        expl.setBillboardPointEye()
        seq = Sequence(Wait(seqn.getNumFrames() / seqn.getFrameRate()), Func(root.removeNode))
        seq.start()



from tf.entity.DistributedEntity import DistributedEntity

from panda3d.core import *
from panda3d.pphysics import *

from direct.directbase import DirectRender
from tf.tfbase.TFGlobals import Contents, TakeDamage

from math import pow

class World(DistributedEntity):

    def __init__(self):
        DistributedEntity.__init__(self)
        self.takeDamageMode = TakeDamage.No

    def generate(self):
        DistributedEntity.generate(self)
        base.world = self

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        if IS_CLIENT:
            base.game.worldLoaded()

if not IS_CLIENT:
    WorldAI = World
    WorldAI.__name__ = 'WorldAI'

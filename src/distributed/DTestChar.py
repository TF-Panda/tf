
from tf.actor.DistributedChar import DistributedChar

from panda3d.core import *

class DTestChar(DistributedChar):

    def announceGenerate(self):
        DistributedChar.announceGenerate(self)
        self.reparentTo(base.dynRender)

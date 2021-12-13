
from tf.actor.DistributedCharAI import DistributedCharAI
from tf.actor.Activity import Activity

from panda3d.core import *

class DTestCharAI(DistributedCharAI):

    def generate(self):
        DistributedCharAI.generate(self)
        self.setModel("models/char/engineer")
        self.tauntSeqs = self.getSequencesForActivity(Activity.Taunt)
        self.tauntSeq = 0
        self.resetSequence(self.tauntSeqs[self.tauntSeq])

    def simulate(self):
        if self.isCurrentSequenceFinished():
            self.tauntSeq += 1
            self.tauntSeq %= len(self.tauntSeqs)
            self.resetSequence(self.tauntSeqs[self.tauntSeq])
        DistributedCharAI.simulate(self)

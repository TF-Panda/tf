"""DistributedSentryRocket module: contains the DistributedSentryRocket class."""

from tf.weapon.BaseRocket import BaseRocket

from panda3d.pphysics import PhysBox

class DistributedSentryRocket(BaseRocket):

    def __init__(self):
        BaseRocket.__init__(self)
        if IS_CLIENT:
            self.trails = []
        else:
            # Use an 8x8x8 cube to test for hits.
            self.sweepGeometry = PhysBox(8, 8, 8)

    if IS_CLIENT:
        def announceGenerate(self):
            BaseRocket.announceGenerate(self)

            # Start the spinning animation.
            self.setAnim("idle")

            numRockets = 4
            for i in range(numRockets):
                node = self.find("**/rocket" + str(i + 1))
                if not node.isEmpty():
                    trail = self.makeTrailsEffect(node)
                    trail.start(base.dynRender)
                    self.trails.append(trail)

        def disable(self):
            for trail in self.trails:
                trail.softStop()
            self.trails = None
            BaseRocket.disable(self)

    else:
        def generate(self):
            self.setModel("models/buildables/sentry3_rockets")
            BaseRocket.generate(self)

if not IS_CLIENT:
    DistributedSentryRocketAI = DistributedSentryRocket
    DistributedSentryRocketAI.__name__ = 'DistributedSentryRocketAI'

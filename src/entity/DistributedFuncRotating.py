"""DistributedFuncRotating module: contains the DistributedFuncRotating class."""

from .DistributedSolidEntity import DistributedSolidEntity

class DistributedFuncRotating(DistributedSolidEntity):
    """
    A rotating brush.
    """

    StartOn = 1
    ReverseDirection = 2
    XAxis = 4
    YAxis = 8
    AccelerateDecelerate = 16
    NotSolid = 64

    def __init__(self):
        DistributedSolidEntity.__init__(self)
        self.rotation = 0.0
        self.rotateSpeed = 0.0
        self.spawnflags = 0

    if not IS_CLIENT:
        def initFromLevel(self, ent, props):
            DistributedSolidEntity.initFromLevel(self, ent, props)
            if props.hasAttribute("maxspeed"):
                self.rotateSpeed = props.getAttributeValue("maxspeed").getFloat()
            if props.hasAttribute("spawnflags"):
                self.spawnflags = props.getAttributeValue("spawnflags").getInt()
    else:
        def announceGenerate(self):
            DistributedSolidEntity.announceGenerate(self)
            if self.spawnflags & self.StartOn:
                self.startRotating()

        #def input_Start(self):
        #    self.startRotating()

        #def input_Stop(self):
        #    self.stopRotating()

        def startRotating(self):
            self.addTask(self.__rotate, 'func_rotating_rotate', appendTask=True, sim=False)

        def __rotate(self, task):
            inc = globalClock.dt * self.rotateSpeed
            if self.spawnflags & self.ReverseDirection:
                self.rotation -= inc
            else:
                self.rotation += inc
            self.setH(self.rotation)
            return task.cont

        def stopRotating(self):
            self.removeTask('func_rotating_rotate')

if not IS_CLIENT:
    DistributedFuncRotatingAI = DistributedFuncRotating
    DistributedFuncRotatingAI.__name__ = 'DistributedFuncRotatingAI'

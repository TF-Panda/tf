"""KillFeed module: contains the KillFeed class."""

from panda3d.core import *
from direct.gui.DirectGui import *

from tf.tfbase import TFGlobals

class KillFeedEvent:

    def __init__(self, lbl, priority, time):
        self.lbl = lbl
        self.priority = priority
        self.time = time

class KillFeed:

    def __init__(self):
        self.node = base.a2dTopRight.attachNewNode("killFeed")
        self.node.setPos(-0.1, 0, -0.1)
        self.topPos = 0.0
        self.eventSpacing = 0.065
        self.priorityLife = 15
        self.defaultLife = 10
        self.events = []
        self.maxEvents = 6

        base.taskMgr.add(self.__update, 'updateKillFeed')

    def cleanup(self):
        base.taskMgr.remove('updateKillFeed')
        for ev in self.events:
            ev.lbl.destroy()
        self.events = None
        self.node.removeNode()
        self.node = None

    def pushEvent(self, text, priority):
        lbl = OnscreenText(text=text, scale=0.045, bg=(0.4, 0.4, 0.4, 1), fg=(1, 1, 1, 1),
                           parent=self.node, align=TextNode.ARight, font=TFGlobals.getTF2SecondaryFont())
        if priority:
            lbl['fg'] = (0.0, 0.0, 0.0, 1)
            lbl['bg'] = (1, 1, 1, 1)
        lbl.hide()

        self.events.append(KillFeedEvent(lbl, priority, globalClock.getFrameTime()))

    def __update(self, task):
        self.sortEvents()
        return task.cont

    def sortEvents(self):
        now = globalClock.getFrameTime()

        # Collect the non-priority vs priority events.
        priorityEvents = []
        nonPriorityEvents = []

        origEvents = list(self.events)

        for ev in self.events:
            ev.lbl.hide()
            if ev.priority:
                priorityEvents.append(ev)
            else:
                nonPriorityEvents.append(ev)

        self.events = []

        # Sort each by time.
        priorityEvents.sort(key=lambda x: x.time)
        nonPriorityEvents.sort(key=lambda x: x.time)

        # Remove expired.
        priorityEvents[:] = [x for x in priorityEvents if now - x.time < self.priorityLife]
        nonPriorityEvents[:] = [x for x in nonPriorityEvents if now - x.time < self.defaultLife]

        count = 0
        i = len(priorityEvents) - 1
        # Add priority first.
        while count < self.maxEvents and i >= 0:
            self.events.append(priorityEvents[i])
            count += 1
            i -= 1

        # Now add the non-priority.
        i = len(nonPriorityEvents) - 1
        while count < self.maxEvents and i >= 0:
            self.events.append(nonPriorityEvents[i])
            count += 1
            i -= 1

        # Sort events.
        self.events.sort(key=lambda x: x.time)

        z = 0.0
        # Position them.
        for ev in self.events:
            ev.lbl.show()
            ev.lbl.setPos(0, z)
            z -= self.eventSpacing

        # Destroy old event labels.
        for ev in origEvents:
            if not ev in self.events:
                ev.lbl.destroy()

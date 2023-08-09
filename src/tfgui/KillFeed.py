"""KillFeed module: contains the KillFeed class."""

from panda3d.core import *

from direct.gui.DirectGui import *
from tf.tfbase import TFGlobals


class KillFeedEvent:

    def __init__(self, lbl, priority, time, dur):
        self.lbl = lbl
        self.priority = priority
        self.time = time
        self.expireTime = time + dur

    def cleanup(self):
        self.lbl.destroy()
        self.lbl = None

class KillFeed:

    def __init__(self):
        self.node = base.a2dTopRight.attachNewNode("killFeed")
        self.node.setPos(-0.1, 0, -0.1)
        self.topPos = 0.0
        self.eventSpacing = 0.065
        self.priorityLife = 15
        self.defaultLife = 10
        self.events = []
        self.priorityEvents = []
        self.maxEvents = 6
        self.latestTime = 0.0

        base.taskMgr.add(self.__update, 'updateKillFeed')

    def cleanup(self):
        base.taskMgr.remove('updateKillFeed')
        for ev in self.events:
            ev.lbl.destroy()
        self.events = None
        self.node.removeNode()
        self.node = None

    def pushEvent(self, text, priority):
        lbl = OnscreenText(text=text, scale=0.045, bg=(0.3, 0.3, 0.3, 1), fg=(0.984, 0.925, 0.796, 1.0),
                           parent=self.node, align=TextNode.ARight, font=TFGlobals.getTF2SecondaryFont())
        if priority:
            lbl['fg'] = (0.0, 0.0, 0.0, 1)
            lbl['bg'] = (0.984, 0.925, 0.796, 1.0)
        lbl.hide()

        time = base.clockMgr.getTime()
        if time == self.latestTime:
            # Weird fudge to prevent events with identical times.
            # If two events have identical times the sorting goes weird.
            time += 0.001
        self.latestTime = time

        self.addEvent(KillFeedEvent(lbl, priority, time, self.defaultLife if not priority else self.priorityLife))

    def addEvent(self, event):
        self.events.append(event)

        if len(self.events) > self.maxEvents:
            # Remove oldest non-priority event.
            # However, if they are all priority, remove the oldest.
            remove = None
            for ev in self.events:
                if not ev.priority:
                    remove = ev
                    break
            if not remove:
                remove = self.events[0]
            remove.cleanup()
            self.events.remove(remove)

        self.sortEvents()

    def __update(self, task):
        removedEvents = []

        now = base.clockMgr.getTime()
        for ev in self.events:
            if now >= ev.expireTime:
                removedEvents.append(ev)

        if removedEvents:
            for ev in removedEvents:
                ev.cleanup()
                self.events.remove(ev)
            self.sortEvents()

        return task.cont

    def sortEvents(self):
        # Collect the non-priority vs priority events.
        priorityEvents = []
        nonPriorityEvents = []

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

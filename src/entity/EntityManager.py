"""EntityManager module: contains the EntityManager class."""

import re

class EntityManager:

    def __init__(self):
        self.targetName2ent = {}

    def findEntity(self, pattern):
        return [self.targetName2ent[x] for x in self.targetName2ent.keys() if re.search(pattern, x)]

    def registerEntity(self, ent):
        if ent.targetName:
            self.targetName2ent[ent.targetName] = ent

        print(self.targetName2ent)

    def removeEntity(self, ent):
        if ent.targetName and ent.targetName in self.targetName2ent:
            del self.targetName2ent[ent.targetName]

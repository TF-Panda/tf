"""EntityManager module: contains the EntityManager class."""

import re

from .EntityRegistryAI import EntityRegistry

class EntityManager:

    def __init__(self):
        self.ents = []

    def getEntityClass(self, classname):
        return EntityRegistry.get(classname)

    def makeEntity(self, classname):
        entCls = self.getEntityClass(classname)
        if not entCls:
            return None
        return entCls()

    def findAllEntities(self, pattern):
        ents = []
        for e in self.ents:
            if re.search(pattern, e.targetName):
                ents.append(e)
        return ents

    def findExactEntity(self, name):
        for e in self.ents:
            if e.targetName == name:
                return e
        return None

    def findAllEntitiesByClassName(self, className):
        ents = []
        for e in self.ents:
            if e.className == className:
                ents.append(e)
        return ents

    def registerEntity(self, ent):
        assert ent not in self.ents
        #if ent.targetName:
        self.ents.append(ent)

    def removeEntity(self, ent):
        if ent in self.ents:
            self.ents.remove(ent)

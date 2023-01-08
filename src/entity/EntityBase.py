"""EntityBase module: contains the EntityBase class."""

from direct.showbase.DirectObject import DirectObject

from .EntityConnectionManager import EntityConnectionManager, OutputConnection

class EntityBase(DirectObject):

    def __init__(self):
        self.targetName = ""
        self.className = ""
        if not IS_CLIENT:
            self.connMgr = EntityConnectionManager(self)

    def isNetworkedEntity(self):
        return False

    def initFromLevel(self, ent, properties):
        self.className = ent.getClassName()
        if properties.hasAttribute("targetname"):
            self.targetName = properties.getAttributeValue("targetname").getString()
        base.entMgr.registerEntity(self)

        for i in range(ent.getNumConnections()):
            conn = ent.getConnection(i)
            oconn = OutputConnection()
            # Convert wildcards to python regex wildcard.
            oconn.targetEntityName = conn.getTargetName().replace("*", ".+")
            oconn.inputName = conn.getInputName()
            oconn.once = conn.getRepeat()
            oconn.delay = conn.getDelay()
            for j in range(conn.getNumParameters()):
                param = conn.getParameter(j)
                if param:
                    oconn.parameters.append(param)
            self.connMgr.addConnection(conn.getOutputName(), oconn)

    def generate(self):
        pass

    def announceGenerate(self):
        pass

    def disable(self):
        pass

    def delete(self):
        if not IS_CLIENT:
            if self.connMgr:
                self.connMgr.cleanup()
                self.connMgr = None
            base.entMgr.removeEntity(self)
        self.ignoreAll()

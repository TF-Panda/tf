"""FilterBase module: contains the FilterBase class."""

from .EntityBase import EntityBase

class FilterBase(EntityBase):
    """
    This is a base class for an entity that filters input activation.
    Derived classes implement different filtering criteria.
    """

    def __init__(self):
        EntityBase.__init__(self)
        self.negate = False

    def initFromLevel(self, ent, properties):
        EntityBase.initFromLevel(self, ent, properties)
        if properties.hasAttribute("Negated"):
            strVal = properties.getAttributeValue("Negated").getString()
            # We have to do this because the default fgd is a string saying this
            # rather than the numeric value!!!
            if strVal == "Allow entities that match criteria":
                self.negate = False
            else:
                self.negate = properties.getAttributeValue("Negated").getBool()

    def testFilter(self, activator):
        ret = self.doFilter(activator)
        if self.negate:
            ret = not ret
        if ret:
            self.connMgr.fireOutput("OnPass")
        else:
            self.connMgr.fireOutput("OnFail")
        return ret

    def doFilter(self, activator):
        return True

import copy

from panda3d.core import *
from panda3d.pphysics import *

# SurfaceDefinition by name.
SurfaceProperties = {}
# Maps PhysMaterial instances to the SurfaceDefinition that created it.
SurfacePropertiesByPhysMaterial = {}

class SurfaceDefinition:

    def __init__(self):
        self.name = ""

        self.thickness = 0.0
        self.density = 0.0
        self.friction = 0.0
        self.dampening = 0.0
        self.elasticity = 0.0

        self.stepLeft = ""
        self.stepRight = ""
        self.bulletImpact = ""
        self.scrapeRough = ""
        self.scrapeSmooth = ""
        self.impactHard = ""
        self.impactSoft = ""
        self.break_ = ""
        self.strain = ""

        self.impactDecal = ""

        self.audioReflectivity = 0.0
        self.audioHardnessFactor = 0.0
        self.audioRoughnessFactor = 0.0

        self.scrapeRoughThreshold = 0.0
        self.impactHardThreshold = 0.0

        self.jumpFactor = 0.0
        self.maxSpeedFactor = 0.0
        self.climbable = False
        self.gameMaterial = ""

        self.physMaterial = None

    def getPhysMaterial(self):
        if not self.physMaterial:
            self.physMaterial = PhysMaterial(self.friction, self.friction,
                                             self.elasticity)
            SurfacePropertiesByPhysMaterial[self.physMaterial] = self
        return self.physMaterial

    def makeCopy(self):
        return copy.deepcopy(self)

def loadSurfacePropertiesFile(filename):
    print("Loading surface properties file %s" % filename.getFullpath())

    kv = KeyValues.load(filename)
    if not kv:
        return False

    for i in range(kv.getNumChildren()):
        surfaceBlock = kv.getChild(i)
        surfaceName = surfaceBlock.getName().lower()

        if surfaceBlock.hasKey("base"):
            sdef = SurfaceProperties.get(surfaceBlock.getValue("base").lower())
            if not sdef:
                print("Base %s for surface %s not found" % (surfaceBlock.getValue("base"), surfaceName))
                return False
            sdef = sdef.makeCopy()
        else:
            # If no base, use "default" as base.
            sdef = SurfaceProperties.get("default")
            if sdef:
                sdef = sdef.makeCopy()
            else:
                # This must be the surface definition for "default".
                sdef = SurfaceDefinition()

        sdef.name = surfaceName

        for j in range(surfaceBlock.getNumKeys()):
            key = surfaceBlock.getKey(j).lower()
            value = surfaceBlock.getValue(j)

            if key == "thickness":
                sdef.thickness = float(value)
            elif key == "density":
                sdef.density = float(value)
            elif key == "friction":
                sdef.friction = float(value)
            elif key == "dampening":
                sdef.dampening = float(value)
            elif key == "audioreflectivity":
                sdef.audioReflectivity = float(value)
            elif key == "audiohardnessfactor":
                sdef.audioHardnessFactor = float(value)
            elif key == "audioroughnessfactor":
                sdef.audioRoughnessFactor = float(value)
            elif key == "scraperoughthreshold":
                sdef.scrapeRoughThreshold = float(value)
            elif key == "impacthardthreshold":
                sdef.impactHardThreshold = float(value)
            elif key == "jumpfactor":
                sdef.jumpFactor = float(value)
            elif key == "maxspeedfactor":
                sdef.maxSpeedFactor = float(value)
            elif key == "climbable":
                sdef.climbable = bool(float(value))
            elif key == "stepleft":
                sdef.stepLeft = value
            elif key == "stepright":
                sdef.stepRight = value
            elif key == "bulletimpact":
                sdef.bulletImpact = value
            elif key == "scraperough":
                sdef.scrapeRough = value
            elif key == "scrapesmooth":
                sdef.scrapeSmooth = value
            elif key == "impacthard":
                sdef.impactHard = value
            elif key == "impactsoft":
                sdef.impactSoft = value
            elif key == "gamematerial":
                sdef.gameMaterial = value
            elif key == "break":
                sdef.break_ = value
            elif key == "strain":
                sdef.strain = value
            elif key == "impactdecal":
                sdef.impactDecal = value

        SurfaceProperties[surfaceName] = sdef

    return True

def loadSurfaceProperties():
    manifestFilename = Filename.fromOsSpecific("scripts/surfaceproperties_manifest.txt")
    manKv = KeyValues.load(manifestFilename)
    if not manKv:
        print("ERROR: Couldn't load surfaceproperties_manifest.txt")
        return False

    manBlock = manKv.getChild(0)
    for i in range(manBlock.getNumKeys()):
        key = manBlock.getKey(i)
        if key == "file":
            spFilename = Filename.fromOsSpecific(manBlock.getValue(i))
            if not loadSurfacePropertiesFile(spFilename):
                print("ERROR: Couldn't load %s from manifest file" % spFilename.getFullpath())
                return False

    return True

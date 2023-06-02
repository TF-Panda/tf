
from panda3d.core import *

suffixes = [
    "rt",
    "bk",
    "lf",
    "ft",
    "up",
    "dn"
]

texorder = [0,2,1,3,4,5]

class SkyBox:

    def __init__(self, skyName = "sky_well_01_hdr", parent=None):
        if not parent:
            parent = base.sky2DCamNp

        self.root = loader.loadModel("models/effects/skybox")
        self.root.reparentTo(parent)
        self.root.setScale(512)

        for i in range(6):
            face = suffixes[texorder[i]]
            faceNp = self.root.find("**/" + face)
            faceNp.setMaterial(MaterialPool.loadMaterial("materials/" + skyName + face + ".mto"))

        self.root.setBin("background", 0)
        self.root.setDepthWrite(True)
        self.root.flattenStrong()
        self.root.setCompass()

    def destroy(self):
        self.root.removeNode()
        self.root = None

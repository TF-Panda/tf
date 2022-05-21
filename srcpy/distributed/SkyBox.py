
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

    def __init__(self, skyName = "sky_well_01_hdr"):
        self.root = base.render.attachNewNode("skybox")

        for i in range(6):
            cm = CardMaker('cm')
            cm.setFrame(-1, 1, -1, 1)
            card = self.root.attachNewNode(cm.generate())
            card.setMaterial(MaterialPool.loadMaterial("tfmodels/src/materials/" + skyName + suffixes[texorder[i]] + ".pmat"))
            card.setShaderInput("u_zFar_index", Vec2(base.camLens.getFar(), i))

        self.root.setBin("background", 0)
        self.root.setDepthWrite(False)
        #self.root.setTwoSided(True)
        self.root.flattenStrong()
        self.root.node().setBounds(OmniBoundingVolume())
        self.root.node().setFinal(True)

    def destroy(self):
        self.root.removeNode()
        self.root = None

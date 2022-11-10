"""DecalRegistry module: contains the DecalRegistry class."""

from panda3d.core import Vec3

Decals = {
  'concrete': {
    'materials': (
      ('tfmodels/src/materials/decals_mod2x.pmat', (0, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (64, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (0, 64), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (64, 64), (64, 64))
    ),
    'size': Vec3(10.24, 10.24, 10.24)
  },

  'metal': {
    'materials': (
      ('tfmodels/src/materials/decals_mod2x.pmat', (128, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (192, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (128, 64), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (192, 64), (64, 64))
    ),
    'size': Vec3(6.4)
  },

  'wood': {
    'materials': (
      ('tfmodels/src/materials/decals_mod2x.pmat', (256, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (320, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (384, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (256, 64), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (320, 64), (64, 64))
    ),
    'size': Vec3(6.4)
  },

  'dirt': {
    'materials': (
      ('tfmodels/src/materials/decals_mod2x.pmat', (576, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (640, 0), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (576, 64), (64, 64)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (640, 64), (64, 64))
    ),
    'size': Vec3(6.4)
  },

  'glass': {
    'materials': (
      ('tfmodels/src/materials/decals_mod2x.pmat', (0, 128), (128, 128)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (128, 128), (128, 128)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (256, 128), (128, 128)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (0, 256), (128, 128)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (128, 256), (128, 128))
    ),
    'size': Vec3(14.08)
  },

  'blood': {
    'materials': (
      'tfmodels/src/materials/decal_blood1.pmat',
      'tfmodels/src/materials/decal_blood2.pmat',
      'tfmodels/src/materials/decal_blood3.pmat',
      'tfmodels/src/materials/decal_blood4.pmat',
      'tfmodels/src/materials/decal_blood5.pmat',
      'tfmodels/src/materials/decal_blood6.pmat'
    ),
    'size': Vec3(20.48, 10.24, 20.48)
  },

  'scorch': {
    'materials': (
      ('tfmodels/src/materials/decals_mod2x.pmat', (512, 256), (256, 256)),
      ('tfmodels/src/materials/decals_mod2x.pmat', (728, 256), (256, 256)),
    ),
    'size': Vec3(166.4, 16, 166.4)
  }
}

"""DecalRegistry module: contains the DecalRegistry class."""

from panda3d.core import Vec3

Decals = {
  'concrete': {
    'materials': (
      ('materials/decals_mod2x.mto', (0, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (64, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (0, 64), (64, 64)),
      ('materials/decals_mod2x.mto', (64, 64), (64, 64))
    ),
    'size': Vec3(10.24, 10.24, 10.24)
  },

  'metal': {
    'materials': (
      ('materials/decals_mod2x.mto', (128, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (192, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (128, 64), (64, 64)),
      ('materials/decals_mod2x.mto', (192, 64), (64, 64))
    ),
    'size': Vec3(6.4)
  },

  'wood': {
    'materials': (
      ('materials/decals_mod2x.mto', (256, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (320, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (384, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (256, 64), (64, 64)),
      ('materials/decals_mod2x.mto', (320, 64), (64, 64))
    ),
    'size': Vec3(6.4)
  },

  'dirt': {
    'materials': (
      ('materials/decals_mod2x.mto', (576, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (640, 0), (64, 64)),
      ('materials/decals_mod2x.mto', (576, 64), (64, 64)),
      ('materials/decals_mod2x.mto', (640, 64), (64, 64))
    ),
    'size': Vec3(6.4)
  },

  'glass': {
    'materials': (
      ('materials/decals_mod2x.mto', (0, 128), (128, 128)),
      ('materials/decals_mod2x.mto', (128, 128), (128, 128)),
      ('materials/decals_mod2x.mto', (256, 128), (128, 128)),
      ('materials/decals_mod2x.mto', (0, 256), (128, 128)),
      ('materials/decals_mod2x.mto', (128, 256), (128, 128))
    ),
    'size': Vec3(14.08)
  },

  'blood': {
    'materials': (
      'materials/decal_blood1.mto',
      'materials/decal_blood2.mto',
      'materials/decal_blood3.mto',
      'materials/decal_blood4.mto',
      'materials/decal_blood5.mto',
      'materials/decal_blood6.mto'
    ),
    'size': Vec3(20.48, 10.24, 20.48)
  },

  'scorch': {
    'materials': (
      ('materials/decals_mod2x.mto', (512, 256), (256, 256)),
      ('materials/decals_mod2x.mto', (728, 256), (256, 256)),
    ),
    'size': Vec3(166.4, 16, 166.4)
  }
}

"""DecalRegistry module: contains the DecalRegistry class."""

from panda3d.core import Vec3

Decals = {
  'concrete': {
    'materials': [
      'tfmodels/src/materials/concrete_decal_shot1.pmat',
      'tfmodels/src/materials/concrete_decal_shot2.pmat',
      'tfmodels/src/materials/concrete_decal_shot3.pmat',
      'tfmodels/src/materials/concrete_decal_shot4.pmat',
      'tfmodels/src/materials/concrete_decal_shot5.pmat'
    ],
    'size': Vec3(10.24, 10.24, 10.24)
  },

  'blood': {
    'materials': [
      'tfmodels/src/materials/blood_decal1.pmat',
      'tfmodels/src/materials/blood_decal2.pmat',
      'tfmodels/src/materials/blood_decal3.pmat',
      'tfmodels/src/materials/blood_decal4.pmat',
      'tfmodels/src/materials/blood_decal5.pmat',
      'tfmodels/src/materials/blood_decal6.pmat'
    ],
    'size': Vec3(20.48, 10.24, 20.48)
  }
}

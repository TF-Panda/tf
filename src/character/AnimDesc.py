from panda3d.core import *

def processAnimDesc(desc, char):

    # First do the weight lists.
    weightlistDescs = desc.get('weight_lists', {})
    weightLists = {}

    for name, joints in weightlistDescs.items():
        wlDesc = WeightListDesc(name)
        for jointName, weight in joints.items():
            wlDesc.setWeight(jointName, weight)
        wl = WeightList(char, desc)
        weightLists[name] = wl

    # Now animations
    animDescs = desc.get('anims', {})

    for name, data in


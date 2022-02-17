
from tf.tfbase.TFGlobals import DamageType
from .TakeDamageInfo import *

from panda3d.core import Quat, Vec3

from .WeaponEffects import *

import random

def fireBullets(player, origin, angles, weapon, mode, seed, spread, damage = -1.0, critical = False, tracerOrigin = None):
    """
    Fires some bullets.  Server does damage calculations.  Client would
    theoretically do the effects (when I implement it).
    """

    doEffects = False

    q = Quat()
    q.setHpr(angles)
    forward = q.getForward()
    right = q.getRight()
    up = q.getUp()

    weaponData = weapon.weaponData.get(mode, {})

    fireInfo = {}
    fireInfo['src'] = origin
    if damage < 0.0:
        fireInfo['damage'] = weaponData.get('damage', 1.0)
    else:
        fireInfo['damage'] = int(damage)
    fireInfo['distance'] = weaponData.get('range', 1000000)
    fireInfo['shots'] = 1
    fireInfo['spread'] = Vec3(spread, spread, 0.0)
    fireInfo['ammoType'] = 0
    fireInfo['tracerOrigin'] = tracerOrigin
    #fireInfo['attacker'] =

    # Setup the bullet damage type
    damageType = weapon.damageType
    customDamageType = -1

    # Reset multi-damage structures.
    clearMultiDamage()

    rand = random.Random()

    bulletsPerShot = weaponData.get('bulletsPerShot', 1)
    for i in range(bulletsPerShot):
        rand.seed(seed)

        # Get circular gaussian spread.
        x = rand.uniform(-0.5, 0.5) + rand.uniform(-0.5, 0.5)
        y = rand.uniform(-0.5, 0.5) + rand.uniform(-0.5, 0.5)

        # Initialize the variable firing information
        fireInfo['dirShooting'] = forward + (right * x * spread) + (up * y * spread)
        fireInfo['dirShooting'].normalize()

        # Fire the bullet!
        player.fireBullet(fireInfo, doEffects, damageType, customDamageType)

        # Use new seed for next bullet.
        seed += 1

    # Apply damage if any.
    applyMultiDamage()

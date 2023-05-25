from .TakeDamageInfo import *

from panda3d.core import *

from .WeaponEffects import *

import random

if IS_CLIENT:
    tf_client_lag_comp_debug = ConfigVariableBool("tf-client-lag-comp-debug", False).value
else:
    tf_server_lag_comp_debug = ConfigVariableBool("tf-server-lag-comp-debug", False).value

def fireBullets(player, origin, angles, weapon, mode, seed, spread, damage = -1.0, critical = False, tracerAttachment = None, tracerStagger=0.0, tracerSpread=0.0):
    """
    Fires some bullets.  Server does damage calculations.  Client would
    theoretically do the effects (when I implement it).
    """

    doEffects = False

    if not IS_CLIENT:
        base.air.lagComp.startLagCompensation(player, player.currentCommand)

    elif base.cr.prediction.hasBeenPredicted():
        # Don't see why we would need to predict bullets more than once.  It's only used
        # to create client-side effects like decals and such.  The result of the bullet
        # hit doesn't affect prediction results.
        return

    # Sync hitboxes *after* lag compensation.
    base.net.syncAllHitBoxes()

    doLagCompDebug = __debug__ and tf_client_lag_comp_debug if IS_CLIENT else tf_server_lag_comp_debug
    if doLagCompDebug:
        hitBoxPositions = []
        if IS_CLIENT:
            from tf.actor.DistributedChar import DistributedChar
            for do in DistributedChar.AllChars:
                for h in do.hitBoxes:
                    hitBoxPositions.append(Point3(NodePath(h.body).getNetTransform().getPos()))
        else:
            from tf.actor.DistributedCharAI import DistributedCharAI
            for do in DistributedCharAI.AllChars:
                for h in do.hitBoxes:
                    hitBoxPositions.append(Point3(NodePath(h.body).getNetTransform().getPos()))


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
    fireInfo['shots'] = weaponData.get('bulletsPerShot', 1)
    fireInfo['spread'] = Vec3(spread, spread, 0.0)
    fireInfo['ammoType'] = 0
    fireInfo['tracerAttachment'] = tracerAttachment
    fireInfo['tracerSpread'] = tracerSpread
    fireInfo['weapon'] = weapon
    #fireInfo['attacker'] =

    # Setup the bullet damage type
    damageType = weapon.getWeaponDamageType()
    customDamageType = -1

    # Reset multi-damage structures.
    clearMultiDamage()

    rand = random.Random()

    if doLagCompDebug:
        rayDirs = []

    tracerDelay = 0.0

    bulletsPerShot = weaponData.get('bulletsPerShot', 1)
    for i in range(bulletsPerShot):
        rand.seed(seed)

        # Get circular gaussian spread.
        x = rand.uniform(-0.5, 0.5) + rand.uniform(-0.5, 0.5)
        y = rand.uniform(-0.5, 0.5) + rand.uniform(-0.5, 0.5)

        # Initialize the variable firing information
        fireInfo['dirShooting'] = forward + (right * x * spread) + (up * y * spread)
        fireInfo['dirShooting'].normalize()
        fireInfo['tracerDelay'] = tracerDelay
        tracerDelay += tracerStagger

        if doLagCompDebug:
            rayDirs.append(fireInfo['dirShooting'])

        # Fire the bullet!
        player.fireBullet(fireInfo, doEffects, damageType, customDamageType)

        # Use new seed for next bullet.
        seed += 1

    if doLagCompDebug:
        if not IS_CLIENT:
            # Tell the client where we saw all of the player hitboxes and
            # where we shot the bullet.
            player.sendUpdate('hitBoxDebug', [hitBoxPositions, fireInfo['src'], rayDirs])
        else:
            # Show how we, the client, saw all of the player hitboxes
            # at the time we shot.
            player.clientHitBoxDebug(hitBoxPositions, fireInfo['src'], rayDirs)

    # Apply damage if any.
    applyMultiDamage()

    if not IS_CLIENT:
        base.air.lagComp.finishLagCompensation(player)


from tf.tfbase.TFGlobals import DamageType, TakeDamage

from panda3d.core import Vec3, Point3

import random

class TakeDamageInfo:
    """
    Information about inflicting damage on an entity.
    """

    def __init__(self, *args, **kwargs):
        TakeDamageInfo.init(self, *args, **kwargs)

    def init(self, inflictor = None, attacker = None, damage = 0,
             damageType = DamageType.Generic, killType = 0,
             damageForce = Vec3(0), damagePosition = Point3(0),
             reportedPosition = Point3(0)):

        self.inflictor = inflictor
        self.attacker = attacker
        self.damage = damage
        self.maxDamage = damage
        self.damageType = damageType
        self.killType = killType
        self.damageForce = damageForce
        self.damagePosition = damagePosition
        # Source location of damage.
        self.sourcePosition = reportedPosition
        self.ammoType = -1
        self.baseDamage = -1
        self.customDamage = -1
        self.damageStats = -1

    def getAmmoName(self):
        if self.inflictor is not None:
            return self.inflictor.name
        else:
            return "unknown"

class MultiDamage(TakeDamageInfo):
    """
    Multi-damage.  Used to collect multiple damages in the same frame (i.e.
    shotgun pellets).
    """

    def __init__(self):
        TakeDamageInfo.__init__(self)
        self.init(None)

    def init(self, target, *args, **kwargs):
        self.target = target
        TakeDamageInfo.init(self, *args, **kwargs)

    def isClear(self):
        return self.target is None

g_multiDamage = MultiDamage()

def clearMultiDamage():
    """
    Resets the global multi-damage accumulator.
    """
    g_multiDamage.init(None)

def applyMultiDamage():
    """
    Inflicts conents of global multi-damage register on multi-damage target.
    """
    if not g_multiDamage.target:
        return

    g_multiDamage.target.takeDamage(g_multiDamage)

    clearMultiDamage()

def addMultiDamage(info, entity):
    """
    Add damage to the existing multi-damage, and apply if it won't fit.
    """
    if not entity:
        return

    if entity != g_multiDamage.target:
        applyMultiDamage()
        g_multiDamage.init(entity, inflictor = info.inflictor, attacker = info.attacker,
                           damageType = info.damageType)
        g_multiDamage.customDamage = info.customDamage

    g_multiDamage.damageType |= info.damageType
    g_multiDamage.damage += info.damage
    g_multiDamage.damageForce += info.damageForce
    g_multiDamage.damagePosition = info.damagePosition
    g_multiDamage.sourcePosition = info.sourcePosition
    g_multiDamage.maxDamage = max(g_multiDamage.maxDamage, info.damage)
    g_multiDamage.ammoType = info.ammoType

def calculateBulletDamageForce(info, forceDir, forceOrigin, scale):
    info.damagePosition = forceOrigin
    force = forceDir.normalized()
    force *= 300 # ??? ammo type damage force?
    force *= 1 # phys_pushscale?
    force *= scale
    info.damageForce = force

def impulseScale(targetMass, desiredSpeed):
    """
    Returns an impulse scale required to push an object.
    """
    return targetMass * desiredSpeed

def calculateExplosiveDamageForce(info, forceDir, forceOrigin, scale):
    info.damagePosition = forceOrigin

    clampForce = impulseScale(75, 400)

    # Calculate an impulse large enough to push a 75kg man 4 in/sec per point
    # of damage.
    forceScale = info.baseDamage * impulseScale(75, 4)

    if forceScale > clampForce:
        forceScale = clampForce

    # Fudge blast forces a little bit, so that each victim gets a slightly
    # different trajectory.  This simulates features that usually vary from
    # person-to-person variables such as bodyweight, which are all identical
    # for characters using the same model.
    forceScale *= random.uniform(0.85, 1.15)

    # Calculate the vector and stuff it into the TakeDamageInfo
    force = forceDir.normalized()
    force *= forceScale
    force *= 1 # phys_pushscale?
    force *= scale
    info.damageForce = force

def calculateMeleeDamageForce(info, forceDir, forceOrigin, scale):
    info.damagePosition = forceOrigin

    # Calculate an impulse large enough to push a 75kg man 4 in/sec per point
    # of damage.
    forceScale = info.baseDamage * impulseScale(75, 4)
    force = forceDir.normalized()
    force *= forceScale
    force *= 1 # phys_pushscale?
    force *= scale
    info.damageForce = force

def guessDamageForce(info, forceDir, forceOrigin, scale):
    """
    Try and guess the physics force to use.  This shouldn't be used for any
    damage where the damage force is unknown.
    """
    if info.damageType & DamageType.Bullet:
        calculateBulletDamageForce(info, forceDir, forceOrigin, scale)
    elif info.damageType & DamageType.Blast:
        calculateExplosiveDamageForce(info, forceDir, forceOrigin, scale)
    else:
        calculateMeleeDamageForce(info, forceDir, forceOrigin, scale)


from tf.tfbase.TFGlobals import DamageType, TakeDamage

from panda3d.core import Vec3, Point3

import random

class TakeDamageInfo:
    """
    Information about inflicting damage on an entity.
    """

    def __init__(self):
        self.clear()

    def setDamage(self, dmg):
        self.maxDamage = max(self.damage, dmg)
        self.damage = dmg

    def clear(self):
        self.inflictor = None
        self.attacker = None
        self.damage = 0
        self.damageType = DamageType.Generic
        self.killType = 0
        self.damageForce = Vec3(0)
        self.damagePosition = Point3(0)
        self.sourcePosition = Point3(0)
        self.ammoType = -1
        self.baseDamage = -1
        self.customDamage = -1
        self.damageStats = -1
        self.maxDamage = 0

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

    def clear(self):
        TakeDamageInfo.clear(self)
        self.target = None

    def isClear(self):
        return self.target is None

g_multiDamage = MultiDamage()

def clearMultiDamage():
    """
    Resets the global multi-damage accumulator.
    """
    print("Clear multi damage")
    g_multiDamage.clear()

def applyMultiDamage():
    """
    Inflicts conents of global multi-damage register on multi-damage target.
    """
    if not g_multiDamage.target:
        return

    print("Apply multi damage")

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
        g_multiDamage.clear()
        g_multiDamage.target = entity
        g_multiDamage.inflictor = info.inflictor
        g_multiDamage.attacker = info.attacker
        g_multiDamage.damageType = info.damageType
        g_multiDamage.customDamage = info.customDamage

    print("Add multi damage")
    print("\tForce before", g_multiDamage.damageForce)

    g_multiDamage.damageType |= info.damageType
    g_multiDamage.setDamage(g_multiDamage.damage + info.damage)
    g_multiDamage.damageForce += info.damageForce
    g_multiDamage.damagePositsion = info.damagePosition
    g_multiDamage.sourcePosition = info.sourcePosition
    g_multiDamage.ammoType = info.ammoType

def calculateBulletDamageForce(info, forceDir, forceOrigin, scale):
    info.damagePosition = forceOrigin
    force = forceDir.normalized()
    force *= 1500 # ??? ammo type damage force?
    force *= 1 # phys_pushscale?
    force *= scale
    info.damageForce = Vec3(force)

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

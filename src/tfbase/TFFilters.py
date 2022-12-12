"""TFFilters module: contains various physics query filters"""

from panda3d.pphysics import PhysRayCastResult, PhysSweepResult, PhysSphere
from panda3d.core import *

from tf.tfbase import CollisionGroups

tf_filter_coll = PStatCollector("App:TFFilterQuery:DoFilter")
tf_filter_pytag_coll = PStatCollector("App:TFFilterQuery:DoFilter:GetPythonTag")

ENTITY_TAG = "entity"

def hitBoxes(actor, mask, entity, source):
    """
    If the given entity has hitboxes and the mask contains the CollisionGroups.HitBox
    bit, ignores the entity's collision hull and only checks against the hit
    boxes.
    """

    fromMask = actor.getFromCollideMask()
    if (CollisionGroups.HitBox & mask) == 0:
        # Not checking against hitboxes, ignore hitboxes.
        if (fromMask & CollisionGroups.HitBox) != 0:
            return 0
    else:
        # We are checking against hitboxes.  Ignore the collision hull, unless
        # the entity doesn't actually have hitboxes.
        if entity.hitBoxes:
            # The entity has hitboxes, so ignore anything that isn't a hitbox.
            if (fromMask & CollisionGroups.HitBox) == 0:
                # This isn't a hitbox.
                return 0

    return 1

def ignorePlayers(actor, mask, entity, source):
    """
    Ignores actors that are attached to players.
    """
    if entity.isPlayer():
        return 0
    return 1

def ignoreEnemies(actor, mask, entity, source):
    """
    Ignores entities that are on the opposite team of the source, including
    buildings.
    """
    if entity.team != source.team:
        return 0
    return 1

def ignoreEnemyPlayers(actor, mask, entity, source):
    """
    Ignores players on the opposite team as the source.  Does not ignore
    enemy buildings.
    """
    if (entity.team != source.team) and entity.isPlayer():
        return 0
    return 1

def ignoreEnemyBuildings(actor, mask, entity, source):
    """
    Ignores enemy buildings, but not players.
    """
    if (entity.team != source.team) and entity.isObject():
        return 0
    return 1

def ignoreTeammates(actor, mask, entity, source):
    """
    Ignores entities that are on the same team as the player/source, including
    buildings.
    """
    if entity.team == source.team:
        return 0
    return 1

def ignoreTeammatePlayers(actor, mask, entity, source):
    """
    Ignores other players that are on the same team as the source.
    Does not ignore buildings and other entities.
    """
    if (entity.team == source.team) and entity.isPlayer():
        return 0
    return 1

def ignoreTeammateBuildings(actor, mask, entity, source):
    """
    Ignores only friendly buildings.
    """
    if (entity.team == source.team) and entity.isObject():
        return 0
    return 1

def ignoreSelf(actor, mask, entity, source):
    """
    Ignores the source entity of the query.
    """
    if entity == source:
        return 0
    return 1

def worldOnly(actor, mask, entity, source):
    """
    Only allows the world.
    """
    if entity == base.world:
        return 1
    return 0

class TFQueryFilter:

    def __init__(self, sourceEntity = None, filters = [], ignoreSource = True):
        self.filter = CallbackObject.make(self.__doFilter)
        self.sourceEntity = sourceEntity
        self.ignoreSource = ignoreSource
        self.filters = filters

    def __doFilter(self, cbdata):
        ret = self.doFilter(cbdata.actor, cbdata.into_collide_mask, cbdata.result)
        cbdata.result = ret

    def doFilter(self, actor, mask, hitType):
        """
        Runs the set of Python filters in order.  The filter will early-out
        if one of the filters ignores the query.

        TODO: Move this to C++ if it's too slow.
        """

        entity = actor.getPythonTag(ENTITY_TAG)
        if not entity:
            # It must be associated with an entity.
            return 0

        if self.ignoreSource and entity == self.sourceEntity:
            # Ignore ourselves.
            return 0

        if not hitBoxes(actor, mask, entity, self.sourceEntity):
            return 0

        for f in self.filters:
            retVal = f(actor, mask, entity, self.sourceEntity)
            if not retVal:
                return 0

        return hitType

def makeTraceInfo(start, end, dir, dist, result):
    data = {}
    data['tracestart'] = start
    data['traceend'] = end
    data['tracedir'] = dir
    data['tracedist'] = dist
    data['ret'] = result
    data['hit'] = result.hasBlock()
    if result.hasBlock():
        block = result.getBlock()
        actor = block.getActor()
        data['block'] = block
        data['actor'] = actor
        data['pos'] = block.getPosition()
        data['norm'] = block.getNormal()
        data['mat'] = block.getMaterial()
        data['ent'] = actor.getPythonTag('entity') if actor else None
        data['frac'] = (block.getDistance() / dist) if dist > 0.0 else 0.0
        #assert data['frac'] >= 0.0 and data['frac'] <= 1.0
        data['endpos'] = start + dir * block.getDistance()
        data['startsolid'] = block.getDistance() < 0
    else:
        data['block'] = None
        data['actor'] = None
        data['pos'] = Point3()
        data['norm'] = Vec3()
        data['mat'] = None
        data['ent'] = None
        data['frac'] = 1.0
        data['endpos'] = end
        data['startsolid'] = False
    return data

def traceCalcVector(start, end):
    dir = end - start
    dist = dir.length()
    if not dir.normalize():
        dir = Vec3.forward()
    return (dir, dist)

def traceLine(start, end, intoMask, filter):
    dir, dist = traceCalcVector(start, end)
    result = PhysRayCastResult()
    base.physicsWorld.raycast(result, start, dir, dist, intoMask, 0, filter.filter)
    return makeTraceInfo(start, end, dir, dist, result)

def traceBox(start, end, mins, maxs, intoMask, filter, hpr=Vec3(0)):
    dir, dist = traceCalcVector(start, end)
    result = PhysSweepResult()
    base.physicsWorld.boxcast(result, start + mins, start + maxs, dir, dist,
                              hpr, intoMask, 0, filter.filter)
    return makeTraceInfo(start, end, dir, dist, result)

def traceSphere(start, end, radius, intoMask, filter):
    dir, dist = traceCalcVector(start, end)
    result = PhysSweepResult()
    base.physicsWorld.sweep(result, PhysSphere(radius), start, Vec3(0), dir, dist,
                            intoMask, 0, filter.filter)
    return makeTraceInfo(start, end, dir, dist, result)

def traceGeometry(start, end, geom, intoMask, filter, hpr=Vec3(0)):
    dir, dist = traceCalcVector(start, end)
    result = PhysSweepResult()
    base.physicsWorld.sweep(result, geom, start, hpr, dir, dist, intoMask, 0, filter.filter)
    return makeTraceInfo(start, end, dir, dist, result)

def clipVelocity(inVel, normal, outVel, overBounce):
    angle = normal.z

    blocked = 0
    if angle > 0:
        blocked |= 1
    if not angle:
        blocked |= 2

    # Determine how far along plane to slide based on incoming direction.
    backoff = inVel.dot(normal) * overBounce

    for i in range(3):
        change = normal[i] * backoff
        outVel[i] = inVel[i] - change

    # Iterate once to make sure we aren't still moving through the plane.
    adjust = outVel.dot(normal)
    if adjust < 0.0:
        outVel.assign(outVel - normal * adjust)

    return blocked

def collideAndSlide(origin, velocity, collInfo, intoMask, filter):
    """
    Origin: current object position.
    Velocity: desired movement offset
    Mins: object bbox mins (origin relative)
    Maxs: object bbox maxs (origin relative)

    Velocity is modified in place, contains corrected movement offset.
    """

    origVelocity = Vec3(velocity)
    primalVelocity = Vec3(velocity)

    numBumps = 4
    blocked = 0
    numPlanes = 0
    planes = [Vec3()] * 5

    allFraction = 0.0
    timeLeft = globalClock.dt

    newVelocity = Vec3()

    for bumpCount in range(numBumps):
        if velocity.length() == 0:
            break

        # Assume we can move all the way from the current origin to the
        # end point.
        end = origin + velocity * timeLeft
        if collInfo['type'] == 'box':
            tr = traceBox(origin, end, collInfo['mins'], collInfo['maxs'], intoMask, filter)
        elif collInfo['type'] == 'sphere':
            tr = traceSphere(origin, end, collInfo['radius'], intoMask, filter)
        else:
            assert False
        fraction = tr['frac']

        allFraction += fraction

        # If we moved some portion of the total distance, then
        # copy the end position into the
        if fraction > 0:
        #    if numBumps > 0 and fraction == 1:

            # Actually covered some distance.
            origin.assign(tr['endpos'])
            origVelocity.assign(velocity)
            numPlanes = 0

        if fraction == 1:
            # If we covered the entire distance, we are done and can return.
            break

        # If the plane we hit has a high z component in the normal, then
        # it's probably a floor.
        if tr['norm'].z > 0.7:
            blocked |= 1
        if not tr['norm'].z:
            blocked |= 2

        # Reduce amount of dt left by total time left * fraction that we
        # covered.
        timeLeft -= timeLeft * fraction

        if numPlanes >= 5:
            velocity.set(0, 0, 0)
            break

        # Setup next cliping plane
        planes[numPlanes] = tr['norm']
        numPlanes += 1

        allOk = True
        hadToClip = True
        for i in range(numPlanes):
            clipVelocity(origVelocity, planes[i], velocity, 1)
            ok = True
            for j in range(numPlanes):
                if i == j:
                    continue
                # Are we now moving against this plane.
                if velocity.dot(planes[j]) < 0:
                    ok = False
                    break # not ok
            if ok:
                hadToClip = False
                break

        if hadToClip:
            # Go along the crease
            if numPlanes != 2:
                velocity.set(0, 0, 0)
                break

            dir = planes[0].cross(planes[1])
            dir.normalize()
            d = dir.dot(velocity)
            velocity.assign(dir * d)

        d = velocity.dot(primalVelocity)
        if d <= 0:
            velocity.set(0, 0, 0)
            break

    if allFraction == 0:
        velocity.set(0, 0, 0)

    return blocked

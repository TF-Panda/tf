"""TFFilters module: contains various physics query filters"""

from panda3d.pphysics import PythonPhysQueryFilter, PhysRayCastResult, PhysSweepResult, PhysSphere
from panda3d.core import *

from tf.tfbase.TFGlobals import Contents

tf_filter_coll = PStatCollector("App:TFFilterQuery:DoFilter")
tf_filter_pytag_coll = PStatCollector("App:TFFilterQuery:DoFilter:GetPythonTag")

ENTITY_TAG = "entity"

def hitBoxes(actor, mask, entity, source):
    """
    If the given entity has hitboxes and the mask contains the Contents.HitBox
    bit, ignores the entity's collision hull and only checks against the hit
    boxes.
    """

    contents = actor.getContentsMask().getWord()
    if (mask & Contents.HitBox) == 0:
        # Not checking against hitboxes, ignore hitboxes.
        if (contents & Contents.HitBox) != 0:
            return 0
    else:
        # We are checking against hitboxes.  Ignore the collision hull, unless
        # the entity doesn't actually have hitboxes.
        if len(entity.hitBoxes) > 0:
            # The entity has hitboxes, so ignore anything that isn't a hitbox.
            if (contents & Contents.HitBox) == 0:
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

class TFQueryFilter(PythonPhysQueryFilter):

    def __init__(self, sourceEntity = None, filters = [], ignoreSource = True):
        PythonPhysQueryFilter.__init__(self, self.doFilter)
        self.sourceEntity = sourceEntity
        self.ignoreSource = ignoreSource
        self.filters = filters

    def doFilter(self, actor, mask, collisionGroup, hitType):
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

        if not entity.shouldCollide(collisionGroup, mask):
            # Entity doesn't collide with this.
            return 0

        for f in self.filters:
            retVal = f(actor, mask, entity, self.sourceEntity)
            if not retVal:
                return 0

        return hitType

def traceLine(start, end, contents, cgroup, filter):
    result = PhysRayCastResult()
    dir = end - start
    dist = dir.length()
    if not dir.normalize():
        dir = Vec3.forward()
    base.physicsWorld.raycast(result, start, dir, dist, contents, 0, cgroup, filter)
    data = {}
    data['hit'] = result.hasBlock()
    if result.hasBlock():
        block = result.getBlock()
        actor = block.getActor()
        data['actor'] = actor
        data['pos'] = block.getPosition()
        data['norm'] = block.getNormal()
        data['mat'] = block.getMaterial()
        data['ent'] = actor.getPythonTag('entity') if actor else None
        data['frac'] = (block.getDistance() / dist) if dist > 0.0 else 0.0
        #assert data['frac'] >= 0.0 and data['frac'] <= 1.0
        data['endpos'] = data['pos']
    else:
        data['actor'] = None
        data['pos'] = Point3()
        data['norm'] = Vec3()
        data['mat'] = None
        data['ent'] = None
        data['frac'] = 1.0
        data['endpos'] = end
    return data

def traceBox(start, end, mins, maxs, contents, cgroup, filter):
    result = PhysSweepResult()
    dir = end - start
    dist = dir.length()
    if not dir.normalize():
        dir = Vec3.forward()
    base.physicsWorld.boxcast(result, start + mins, start + maxs, dir, dist,
                              0, contents, 0, cgroup, filter)
    data = {}
    data['hit'] = result.hasBlock()
    if result.hasBlock():
        block = result.getBlock()
        actor = block.getActor()
        data['actor'] = actor
        data['pos'] = block.getPosition()
        data['norm'] = block.getNormal()
        data['mat'] = block.getMaterial()
        data['ent'] = actor.getPythonTag('entity') if actor else None
        data['frac'] = (block.getDistance() / dist) if dist > 0 else 0.0
        #assert data['frac'] >= 0.0 and data['frac'] <= 1.0
        data['endpos'] = start + dir * block.getDistance()
    else:
        data['actor'] = None
        data['pos'] = Point3()
        data['norm'] = Vec3()
        data['mat'] = None
        data['ent'] = None
        data['frac'] = 1.0
        data['endpos'] = end
    return data

def traceSphere(start, end, radius, contents, cgroup, filter):
    result = PhysSweepResult()
    dir = end - start
    dist = dir.length()
    if not dir.normalize():
        dir = Vec3.forward()
    base.physicsWorld.sweep(result, PhysSphere(radius), start, Vec3(0), dir, dist,
                            contents, 0, cgroup, filter)
    data = {}
    data['hit'] = result.hasBlock()
    if result.hasBlock():
        block = result.getBlock()
        actor = block.getActor()
        data['actor'] = actor
        data['pos'] = block.getPosition()
        data['norm'] = block.getNormal()
        data['mat'] = block.getMaterial()
        data['ent'] = actor.getPythonTag('entity') if actor else None
        data['frac'] = (block.getDistance() / dist) if dist > 0 else 0.0
        #assert data['frac'] >= 0.0 and data['frac'] <= 1.0
        data['endpos'] = start + dir * block.getDistance()
    else:
        data['actor'] = None
        data['pos'] = Point3()
        data['norm'] = Vec3()
        data['mat'] = None
        data['ent'] = None
        data['frac'] = 1.0
        data['endpos'] = end
    return data

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

def collideAndSlide(origin, velocity, mins, maxs, contents, collisionGroup, filter):
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
        tr = traceBox(origin, end, mins, maxs, contents, collisionGroup, filter)
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

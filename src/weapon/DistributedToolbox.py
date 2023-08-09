"""DistributedToolbox module: contains the DistributedToolbox class."""

# Toolbox weapon for placing buildings.

from panda3d.core import *

from direct.directbase import DirectRender
from direct.gui.DirectGui import *
from tf.actor.Actor import Actor
from tf.object.ObjectDefs import ObjectDefs
from tf.player.InputButtons import InputFlag
from tf.tfbase import CollisionGroups, TFFilters, TFGlobals, TFLocalizer

from .TFWeapon import TFWeapon
from .WeaponMode import TFWeaponType


class DistributedToolbox(TFWeapon):

    WeaponModel = "models/weapons/w_toolbox"
    WeaponViewModel = "models/weapons/v_toolbox_engineer"
    UsesViewModel = True
    HiddenFromUI = True

    BlueprintOffset = Point3(0, 64, 0)

    GroundClearance = 32

    def __init__(self):
        TFWeapon.__init__(self)
        self.weaponType = TFWeaponType.Building

        self.usesClip = False
        self.usesAmmo = False

        self.rotation = 0

        self.bldgDef = None
        self.buildOrigin = Vec3()
        self.buildMins = Vec3()
        self.buildMaxs = Vec3()
        self.lastDenySound = 0.0

        if IS_CLIENT:
            self.blueprintRoot = NodePath("blueprint_root")
            self.blueprint = None
            self.goodBuild = False

        self.currentRotation = 0.0

    def verifyCorner(self, bottomCenter, ofs):
        # Start slightly above the surface
        start = Vec3(bottomCenter.x + ofs.x, bottomCenter.y + ofs.y, bottomCenter.z + 0.1)

        end = start - Vec3(0, 0, self.GroundClearance)

        #if IS_CLIENT:
        #    base.addOneOffNode(TFGlobals.getLineViz(start, end, 1, (0, 0, 1, 1)))

        tr = TFFilters.traceLine(start, end,
            CollisionGroups.World | CollisionGroups.PlayerClip,
            TFFilters.TFQueryFilter(self.player))
        if tr['hit']:
            # Cannot build on very steep slopes ( > 45 degrees )
            dot = tr['norm'].dot(Vec3.up())
            #print(tr['norm'], dot)
            if dot < 0.65:
                # Too steep.
                return False
            return tr['frac'] > 0 and tr['frac'] < 1
        return False

    def calculatePlacementPos(self):
        hpr = Vec3(0)
        hpr.x = self.player.viewAngles[0]
        q = Quat()
        q.setHpr(hpr)
        fwd = q.getForward()

        self.updateBuildRotation()
        hpr.x += self.currentRotation

        objectRadius = Vec2(
            max(abs(self.buildMins.x), abs(self.buildMaxs.x)),
            max(abs(self.buildMins.y), abs(self.buildMaxs.y))
        )
        localMins = self.player.getLocalHullMins()
        localMaxs = self.player.getLocalHullMaxs()
        playerRadius = Vec2(
            max(abs(localMins.x), abs(localMaxs.x)),
            max(abs(localMins.y), abs(localMaxs.y))
        )

        # Small safety buffer.
        distance = objectRadius.length() + playerRadius.length() + 4

        playerCenter = self.player.getWorldSpaceCenter()

        buildOrigin = playerCenter + fwd * distance

        self.buildOrigin = buildOrigin
        errorOrigin = buildOrigin - (self.buildMaxs - self.buildMins) * 0.5 - self.buildMins

        buildDims = self.buildMaxs - self.buildMins
        halfBuildDims = buildDims * 0.5
        halfBuildDimsXY = Vec3(halfBuildDims.x, halfBuildDims.y, 0.01)

        halfPlayerDims = (localMaxs - localMins) * 0.5
        boxTopZ = playerCenter.z + halfPlayerDims.z + buildDims.z
        boxBottomZ = playerCenter.z - halfPlayerDims.z - buildDims.z

        # First, find the ground (ie: where the bottom of the box goes).
        it = 0
        numIterations = 8
        bottomZ = 0
        topZ = boxTopZ
        topZInc = (boxBottomZ - boxTopZ) / (numIterations - 1)
        while it < numIterations:
            tr = TFFilters.traceBox(Vec3(self.buildOrigin.x, self.buildOrigin.y, topZ),
                                    Vec3(self.buildOrigin.x, self.buildOrigin.y, boxBottomZ),
                                    -halfBuildDimsXY, halfBuildDimsXY, CollisionGroups.World | CollisionGroups.PlayerClip,
                                    TFFilters.TFQueryFilter(self.player), hpr)

            if not tr['hit']:
                # If there is no ground, then we can't place here.
                self.buildOrigin = errorOrigin
                return False

            bottomZ = tr['endpos'].z

            # If we found enough space to fit our object, place here.
            if (topZ - bottomZ > buildDims.z):
                break

            topZ += topZInc

            it += 1

        if it == numIterations:
            self.buildOrigin = errorOrigin
            return False

        # Now see if the range we've got leaves us room for our box.
        if (topZ - bottomZ < buildDims.z):
            self.buildOrigin = errorOrigin
            return False

        # Verify that it's not too much of a slope by seeing how far the corners
        # are from the ground.
        buildQuat = Quat()
        buildQuat.setHpr(hpr)
        buildMat = LMatrix3()
        buildQuat.extractToMatrix(buildMat)
        bottomCenter = Vec3(self.buildOrigin.x, self.buildOrigin.y, bottomZ)
        ll = Vec2(-halfBuildDims.x, -halfBuildDims.y)
        ur = Vec2(halfBuildDims.x, halfBuildDims.y)
        lr = Vec2(halfBuildDims.x, -halfBuildDims.y)
        ul = Vec2(-halfBuildDims.x, halfBuildDims.y)
        if not self.verifyCorner(bottomCenter, buildMat.xformVec(ll)) or \
            not self.verifyCorner(bottomCenter, buildMat.xformVec(ur)) or \
            not self.verifyCorner(bottomCenter, buildMat.xformVec(lr)) or \
            not self.verifyCorner(bottomCenter, buildMat.xformVec(ul)):

            self.buildOrigin = errorOrigin
            return False

        # Ok, now we know the Z range where this box can fit.
        bottomLeft = self.buildOrigin - halfBuildDims
        bottomLeft.z = bottomZ
        self.buildOrigin = bottomLeft - self.buildMins

        return True

    def isPlacementPosValid(self):
        valid = self.calculatePlacementPos()
        if not valid:
            return False

        #if IS_CLIENT:
        #    base.addOneOffNode(TFGlobals.getBoxViz(self.buildOrigin + self.buildMins, self.buildOrigin + self.buildMaxs, 1, (1, 0, 0, 1)))

        # Check that the build hull is not blocked by any players or other buildings.
        tr = TFFilters.traceBox(self.buildOrigin, self.buildOrigin, self.buildMins, self.buildMaxs,
                                CollisionGroups.Mask_AllTeam, TFFilters.TFQueryFilter(self.player))
        if tr['frac'] < 1:
            return False

        # Check that we have a LOS to the build position.
        eyePos = self.player.getEyePosition()
        tr = TFFilters.traceLine(self.buildOrigin, eyePos, CollisionGroups.World | CollisionGroups.Mask_AllTeam,
                                 TFFilters.TFQueryFilter(self.player))
        if tr['frac'] < 1:
            return False

        return True

    def primaryAttack(self):
        TFWeapon.primaryAttack(self)

        if not IS_CLIENT:
            valid = self.isPlacementPosValid()
            built = False
            if valid:
                if self.player.placeObject(self.buildOrigin, self.currentRotation + self.player.viewAngles[0]):
                    # Building placed successfully, go to wrench.
                    self.player.setActiveWeapon(2)
                    built = True
            if not built and (base.clockMgr.getTime() - self.lastDenySound) >= 0.3:
                self.player.emitSound("Player.UseDeny", client=self.player.owner)
                self.lastDenySound = base.clockMgr.getTime()

    if not IS_CLIENT:
        def itemPostFrame(self):
            TFWeapon.itemPostFrame(self)
            self.updateBuildRotation()

    def secondaryAttack(self):
        TFWeapon.secondaryAttack(self)

        # Only rotate on first press of secondary attack.
        if (self.player.buttonsPressed & InputFlag.Attack2) != 0:
            self.rotation += 1
            self.rotation %= 4

    def activate(self):
        if not TFWeapon.activate(self):
            return False

        self.rotation = 0

        self.currentRotation = 0.0

        self.lastDenySound = 0.0

        self.bldgDef = ObjectDefs.get(self.player.selectedBuilding)
        assert self.bldgDef

        self.buildMins = self.bldgDef['buildhull'][0]
        self.buildMaxs = self.bldgDef['buildhull'][1]

        if IS_CLIENT and self.isOwnedByLocalPlayer():
            # Load the blueprint and place in front of player.
            self.goodBuild = True
            if self.blueprint:
                self.blueprint.removeNode()
            self.blueprint = Actor()
            self.blueprint.loadModel(self.bldgDef['blueprint'])
            self.blueprint.setSkin(self.player.team)
            self.blueprint.setAnim('idle', loop=True)
            self.blueprint.modelNp.reparentTo(self.blueprintRoot)
            self.blueprint.modelNp.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
            self.blueprint.modelNp.showThrough(DirectRender.ShadowCameraBitmask)
            self.blueprintRoot.reparentTo(base.render)

            self.addTask(self.updateRotation, 'updateBlueprintRotation', appendTask=True, sim=False, sort=49)

    def deactivate(self):
        if IS_CLIENT and self.isOwnedByLocalPlayer():
            if self.blueprint:
                self.blueprint.cleanup()
                self.blueprint = None
            self.blueprintRoot.reparentTo(base.hidden)
            self.removeTask('updateBlueprintRotation')

        TFWeapon.deactivate(self)

    def updateBuildRotation(self):
        ROTATE_SPEED = 250.0
        targetRotation = self.rotation * 90.0
        self.currentRotation = TFGlobals.approachAngle(targetRotation, self.currentRotation, ROTATE_SPEED * base.clockMgr.getDeltaTime())

    if IS_CLIENT:
        def addPredictionFields(self):
            TFWeapon.addPredictionFields(self)
            self.addPredictionField("buildOrigin", Vec3, tolerance=0.01)
            self.addPredictionField("buildMins", Vec3, tolerance=0)
            self.addPredictionField("buildMaxs", Vec3, tolerance=0)
            self.addPredictionField("rotation", int)

        def updateRotation(self, task):
            valid = self.isPlacementPosValid()

            self.blueprintRoot.setPos(self.buildOrigin)
            self.blueprintRoot.setH(self.player.viewAngles[0])

            if not valid:
                if self.goodBuild:
                    self.goodBuild = False
                    self.blueprint.setAnim('reject', loop=True)
            else:
                if not self.goodBuild:
                    self.goodBuild = True
                    self.blueprint.setAnim('idle', loop=True)

            if self.blueprint:
                self.blueprint.modelNp.setH(self.currentRotation)

            return task.cont

    def getName(self):
        return TFLocalizer.Toolbox

if not IS_CLIENT:
    DistributedToolboxAI = DistributedToolbox
    DistributedToolboxAI.__name__ = 'DistributedToolboxAI'

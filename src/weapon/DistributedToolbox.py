"""DistributedToolbox module: contains the DistributedToolbox class."""

# Toolbox weapon for placing buildings.

from .TFWeapon import TFWeapon

from .WeaponMode import TFWeaponType, TFWeaponMode

from tf.tfbase import TFLocalizer, TFGlobals
from direct.gui.DirectGui import *
from tf.actor.Activity import Activity
from tf.player.PlayerAnimEvent import PlayerAnimEvent
from tf.player.InputButtons import InputFlag

from direct.directbase import DirectRender
from direct.actor.Actor import Actor

from panda3d.core import *

class DistributedToolbox(TFWeapon):

    WeaponModel = "models/weapons/w_toolbox"
    WeaponViewModel = "models/weapons/v_toolbox_engineer"
    UsesViewModel = True
    HiddenFromUI = True

    BlueprintOffset = Point3(0, 64, 0)

    Blueprints = [
        "models/buildables/sentry1_blueprint",
        "models/buildables/dispenser_blueprint",
        "models/buildables/teleporter_blueprint_enter",
        "models/buildables/teleporter_blueprint_exit"
    ]

    def __init__(self):
        TFWeapon.__init__(self)
        self.weaponType = TFWeaponType.Building

        self.usesClip = False
        self.usesAmmo = False

        self.rotation = 0

        if IS_CLIENT:
            self.blueprintRoot = NodePath("blueprint_root")
            self.blueprint = None

        self.currentRotation = 0.0

    def primaryAttack(self):
        TFWeapon.primaryAttack(self)

        if not IS_CLIENT:
            if self.player.placeSentry(self.currentRotation + self.player.viewAngles[0]):
                # Building placed successfully, go to wrench.
                self.player.setActiveWeapon(2)

    if not IS_CLIENT:
        def itemPostFrame(self):
            TFWeapon.itemPostFrame(self)
            self.updateBuildRotation()

    def secondaryAttack(self):
        TFWeapon.secondaryAttack(self)

        # Only rotate on first press of secondary attack.
        if not IS_CLIENT and (self.player.buttonsPressed & InputFlag.Attack2) != 0:
            self.rotation += 1
            self.rotation %= 4

    def activate(self):
        if not TFWeapon.activate(self):
            return False

        if not IS_CLIENT:
            self.rotation = 0.0

        self.currentRotation = 0.0

        if IS_CLIENT and self.isOwnedByLocalPlayer():
            # Load the blueprint and place in front of player.
            if self.blueprint:
                self.blueprint.removeNode()
            self.blueprint = Actor()
            self.blueprint.loadModel(self.Blueprints[self.player.selectedBuilding], keepModel=True)
            modelNode = self.blueprint.getPartModel().node()
            if self.player.team < modelNode.getNumMaterialGroups():
                modelNode.setActiveMaterialGroup(self.player.team)
            self.blueprint.loop('idle')
            self.blueprint.reparentTo(self.blueprintRoot)
            self.blueprint.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
            self.blueprint.showThrough(DirectRender.ShadowCameraBitmask)
            self.blueprintRoot.reparentTo(base.render)

            self.addTask(self.updateRotation, 'updateBlueprintRotation', appendTask=True, sim=False, sort=49)

    def deactivate(self):
        if IS_CLIENT and self.isOwnedByLocalPlayer():
            if self.blueprint:
                self.blueprint.delete()
                self.blueprint = None
            self.blueprintRoot.reparentTo(base.hidden)
            self.removeTask('updateBlueprintRotation')

        TFWeapon.deactivate(self)

    def updateBuildRotation(self):
        ROTATE_SPEED = 250.0
        targetRotation = self.rotation * 90.0
        self.currentRotation = TFGlobals.approachAngle(targetRotation, self.currentRotation, ROTATE_SPEED * globalClock.dt)

    if IS_CLIENT:
        def updateRotation(self, task):
            q = Quat()
            q.setHpr((self.player.viewAngles[0], 0, 0))
            fwd = q.getForward()
            self.blueprintRoot.setPos(self.player.getPos() + fwd * 64)
            self.blueprintRoot.setH(self.player.viewAngles[0])

            self.updateBuildRotation()
            #print("target", self.rotation * 90.0, "current", self.currentRotation)

            if self.blueprint:
                self.blueprint.setH(self.currentRotation)

            return task.cont

    def getName(self):
        return TFLocalizer.Toolbox

if not IS_CLIENT:
    DistributedToolboxAI = DistributedToolbox
    DistributedToolboxAI.__name__ = 'DistributedToolboxAI'

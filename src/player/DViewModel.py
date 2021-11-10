
from tf.character.DistributedChar import DistributedChar

from .DViewModelShared import DViewModelShared

from panda3d.core import *
from panda3d.direct import InterpolatedQuat

class ViewInfo:
    pass

class BobState:

    def __init__(self):
        self.bobTime = 0
        self.lastBobTime = 0
        self.lastSpeed = 0
        self.verticalBob = 0
        self.lateralBob = 0

cl_wpn_sway_interp = 0.1
cl_wpn_sway_scale = 5.0

class DViewModel(DistributedChar, DViewModelShared):

    def __init__(self):
        DistributedChar.__init__(self)
        DViewModelShared.__init__(self)
        self.lastFacing = Vec3()
        self.bobState = BobState()
        self.lagAngles = Quat()
        self.ivLagAngles = InterpolatedQuat()
        self.ivLagAngles.setInterpolationAmount(cl_wpn_sway_interp)
        self.doAnimDebug = False
        self.accept('u', self.toggleAnimDebug)

    def toggleAnimDebug(self):
        self.doAnimDebug = not self.doAnimDebug

    def debugAnim(self):
        if not self.character or not self.doAnimDebug:
            return
        self.character.setAutoAdvanceFlag(False)
        layer = self.character.getAnimLayer(0)
        print("\n")
        print("curtime", globalClock.getFrameTime())
        print("channel", layer._sequence)
        print("cycle", layer._cycle)
        print("flags", layer._flags)
        print("prev time", layer._last_advance_time)
        print("play mode", layer._play_mode)
        print("predictable", self.predictable)
        print("Client side anim", self.clientSideAnimation)

    def simulate(self):
        self.debugAnim()
        DistributedChar.simulate(self)

    def calcView(self, player, camera):
        """
        Main rountine to calculate the position and orientation of the view
        model.  Follows the camera, but applies bob, lag, and sway.
        """

        info = ViewInfo()
        info.originalAngles = camera.getQuat()
        info.angles = camera.getQuat()
        info.origin = camera.getPos()

        if self.player:
            wpn = self.player.getActiveWeaponObj()
            if wpn:
                # Add weapon-specific bob.
                wpn.addViewModelBob(self, info)

        # Add model-specific bob even if no weapon associated (for head bob for off hand models)
        self.addViewModelBob(player, info)
        # Add lag.
        self.calcViewModelLag(info)

        self.setPos(info.origin)
        self.setQuat(info.angles)

        #print("vm view is", info.origin, info.angles.getHpr())

    def addViewModelBob(self, player, info):
        pass

    def calcViewModelLag(self, info):
        self.calcViewModelLag_TF(info)

    def calcViewModelLag_TF(self, info):
        """
        tf_viewmodel lag
        """

        if cl_wpn_sway_interp <= 0.0:
            return

        # Calculate our drift
        forward = info.angles.getForward()
        right = info.angles.getRight()
        up = info.angles.getUp()

        # Add an entry to the history.
        self.ivLagAngles.recordValue(info.angles, globalClock.getFrameTime(), False)

        # Interpolate back 100 ms.
        self.ivLagAngles.interpolate(globalClock.getFrameTime())

        lagAngles = self.ivLagAngles.getInterpolatedValue()

        # Now take the 100ms angle difference and figure out how far the forward vector
        # moved in local space.
        invAngles = Quat()
        invAngles.invertFrom(info.angles)
        angleDiff = lagAngles * invAngles
        laggedForward = angleDiff.getForward()
        forwardDiff = laggedForward - Vec3.forward()
        forwardDiff *= cl_wpn_sway_scale

        # Now offset the origin using that
        info.origin += forward * forwardDiff[1] + right * forwardDiff[0] + up * forwardDiff[2]

    def calcViewModelLag_HL2(self, info):
        """
        baseviewmodel lag
        """
        origPos = Vec3(info.origin)
        origAng = Quat(info.angles)

        maxViewModelLag = 1.5

        # calculate our drift
        forward = info.angles.getForward()

        if globalClock.getDt() != 0.0:
            difference = forward - self.lastFacing

            speed = 5.0

            diff = difference.length()
            if (diff > maxViewModelLag) and (maxViewModelLag > 0.0):
                scale = diff / maxViewModelLag
                speed *= scale

            self.lastFacing += difference * (speed * globalClock.getDt())
            self.lastFacing.normalize()
            info.origin += difference * -5.0

        forward = origAng.getForward()
        right = origAng.getRight()
        up = origAng.getUp()
        hpr = origAng.getHpr()

        pitch = hpr[1]
        if (pitch > 180.0):
            pitch -= 360
        elif (pitch < -180.0):
            pitch += 360

        if maxViewModelLag == 0.0:
            info.origin = origPos
            info.angles = origAng

        info.origin += forward * (-pitch * 0.035)
        info.origin += right * (-pitch * 0.03)
        info.origin += up * (-pitch * 0.02)

    def update(self):
        DistributedChar.update(self)
        if self.playerId != -1 and self.player is None:
            # Poll for the player.
            self.updatePlayer()

    #def update(self):
    #    DistributedChar.update(self)#

    #    if self.character:
    #        self.character.update()
    #        print("VM anim time", self.getAnimTime())
    #        print("VM cycle:", self.getCycle())
    #        print("VM seq:", self.getCurrSequence())

    def shouldPredict(self):
        if self.playerId == base.localAvatarId:
            return True
        return DistributedChar.shouldPredict(self)
        #return False

    def disable(self):
        if self.player:
            self.player.viewModel = None
            self.player = None
        if hasattr(base, 'localAvatarId'):
            if self.playerId == base.localAvatarId:
                self.reparentTo(hidden)
        DistributedChar.disable(self)

    def updatePlayer(self):
        self.player = base.cr.doId2do.get(self.playerId)
        if self.player:
            self.player.viewModel = self
        if self.playerId == base.localAvatarId:
            self.reparentTo(base.vmRender)
        else:
            self.reparentTo(hidden)

    def RecvProxy_playerId(self, playerId):
        self.playerId = playerId
        self.updatePlayer()

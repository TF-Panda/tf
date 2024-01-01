import random

from panda3d.core import *
from panda3d.pphysics import *

from direct.directbase import DirectRender
from direct.interval.IntervalGlobal import (Func, LerpColorScaleInterval,
                                            Parallel, Sequence, Wait)
from tf.actor.Model import Model
from tf.tfbase import CollisionGroups, TFEffects
from tf.tfbase.SurfaceProperties import SurfaceProperties

gibForceUp = 1.0
gibForce = 350.0

class PlayerGibs:

    def __init__(self, pos, hpr, skin, gibInfo, scale=1.0):
        self.gibs = []
        self.headPiece = None

        for i in range(len(gibInfo)):
            partInfo = gibInfo.get(i).getElement()
            mdlFilename = partInfo.getAttributeValue("model").getString()
            isHead = False
            if partInfo.hasAttribute("is_head"):
                isHead = partInfo.getAttributeValue("is_head").getBool()
            mdl = Model()
            mdl.setSkin(skin)
            if not mdl.loadModel(mdlFilename):
                mdl.cleanup()
                continue

            #mdl.modelNp.setTransparency(True)

            surfaceProp = "default"
            customData = mdl.modelData
            if customData is not None:
                if customData.hasAttribute("surfaceprop"):
                    surfaceProp = customData.getAttributeValue("surfaceprop").getString()
            surfaceDef = SurfaceProperties.get(surfaceProp)
            if not surfaceDef:
                physMat = PhysMaterial(1, 1, 0)
            else:
                physMat = surfaceDef.getPhysMaterial()

            # Setup physics for giblet piece.
            cinfo = mdl.modelRootNode.getCollisionInfo()
            cpart = cinfo.getPart(0)
            if cpart.concave:
                cmdata = PhysTriangleMeshData(cpart.mesh_data)
                cmesh = PhysTriangleMesh(cmdata)
            else:
                cmdata = PhysConvexMeshData(cpart.mesh_data)
                cmesh = PhysConvexMesh(cmdata)
            cshape = PhysShape(cmesh, physMat)
            cnode = PhysRigidDynamicNode("gib-%i" % i)
            cnode.addShape(cshape)
            cnode.computeMassProperties()
            cnode.setMass(cpart.mass)
            cnode.setLinearDamping(cpart.damping)
            cnode.setAngularDamping(cpart.rot_damping)
            cnode.setFromCollideMask(CollisionGroups.Debris)
            cnode.setIntoCollideMask(CollisionGroups.World)
            cnode.setCcdEnabled(True)
            cnode.addToScene(base.physicsWorld)
            cnp = base.dynRender.attachNewNode(cnode)
            cnp.node().setFinal(True)
            cnp.setPos(pos)
            cnp.setHpr(hpr)
            cnp.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
            cnp.showThrough(DirectRender.ShadowCameraBitmask)
            cnode.syncTransform()
            mdl.modelNp.reparentTo(cnp)

            partVel = Vec3.up()
            partVel.x += random.uniform(-1.0, 1.0)
            partVel.y += random.uniform(-1.0, 1.0)
            partVel.z += random.uniform(0.0, 1.0)
            partVel.normalize()
            partVel *= gibForce * scale

            #cnode.setLinearVelocity(partVel)

            #print(partVel)

            angImpulse = Vec3(random.uniform(0, 120.0), random.uniform(0, 120.0), 0)
            #cnode.setAngularVelocity(angImpulse)

            cnode.addForce(partVel, cnode.FTVelocityChange)
            cnode.addTorque(angImpulse, cnode.FTVelocityChange)

            if isHead:
                self.headPiece = cnp

            bloodNode = mdl.modelNp.find("**/bloodpoint")
            if bloodNode:
                trailEffect = TFEffects.getBloodTrailEffect()
                trailEffect.setInput(0, bloodNode, False)
                trailEffect.start(base.dynRender)
            else:
                trailEffect = None

            self.gibs.append((cnp, mdl, trailEffect))

        # Fade gibes out after 10 seconds.
        self.fadeOutTask = base.taskMgr.doMethodLater(10.0, self.__fadeGibs, 'fadeGibs')
        self.stopParticlesTask = base.taskMgr.doMethodLater(1.5, self.__stopParticles, 'stopGibParticles')

        self.startedFadeOut = False

        self.valid = True

    def __stopParticles(self, task):
        for _, _, effect in self.gibs:
            if effect:
                effect.softStop()
        return task.done

    def __fadeGibs(self, task):
        if not self.startedFadeOut:
            self.startedFadeOut = True
            for _, mdl, _ in self.gibs:
                mdl.modelNp.setTransparency(True)
        alphaScale = max(0, 1 - (task.time / 0.75))
        if alphaScale == 0:
            self.destroy()
            return task.done
        for _, mdl, _ in self.gibs:
            mdl.modelNp.setAlphaScale(alphaScale)
        return task.cont

    def getHeadPosition(self):
        # Return the world-space COM of the head gib.
        return self.headPiece.getMat(base.render).xformPoint(self.headPiece.node().getCenterOfMass())

    def getHeadMatrix(self):
        # Returns the transform matrix of the world-space COM of the head gib.
        return self.headPiece.getMat(base.render) * LMatrix4.translateMat(self.headPiece.node().getCenterOfMass())

    def destroy(self):
        self.valid = False
        if self.fadeOutTask:
            self.fadeOutTask.remove()
            self.fadeOutTask = None
        if self.stopParticlesTask:
            self.stopParticlesTask.remove()
            self.stopParticlesTask = None
        if self.gibs:
            for gib, mdl, bloodEffect in self.gibs:
                mdl.cleanup()
                gib.node().removeFromScene(base.physicsWorld)
                gib.removeNode()
                if bloodEffect and bloodEffect.isRunning():
                    bloodEffect.softStop()
            self.gibs = None
        self.headPiece = None

""" DistributedGame module: contains the DistributedGame class """

from direct.distributed2.DistributedObject import DistributedObject
from direct.directbase import DirectRender

from panda3d.core import *
from panda3d.pphysics import *

from direct.interval.IntervalGlobal import Sequence, Wait, Func, Parallel, LerpPosInterval, LerpScaleInterval

from tf.tfbase import Sounds

from .DistributedGameBase import DistributedGameBase
from .FogManager import FogManager

play_sound_coll = PStatCollector("App:Sounds:PlaySound")

ClusterColors = [
    LColor(1.0, 0.5, 0.5, 1.0),
    LColor(1.0, 1.0, 0.5, 1.0),
    LColor(1.0, 0.5, 1.0, 1.0),
    LColor(0.5, 1.0, 0.5, 1.0),
    LColor(0.5, 1.0, 1.0, 1.0),
    LColor(0.5, 0.5, 1.0, 1.0)
]

import random

class DistributedGame(DistributedObject, DistributedGameBase):

    def __init__(self):
        DistributedObject.__init__(self)
        DistributedGameBase.__init__(self)

        self.visDebug = False
        self.loadedVisBoxes = False
        self.clusterNodes = None
        self.currentCluster = -1
        self.fogMgr = None

        self.accept('shift-v', self.toggleVisDebug)

    def toggleVisDebug(self):
        self.visDebug = not self.visDebug
        if self.visDebug:
            self.visDebugEnable()
        else:
            self.visDebugDisable()

    def updateVisDebug(self, task):
        # If the cluster changes we have to do work.
        tree = self.lvlData.getAreaClusterTree()
        cluster = tree.getLeafValueFromPoint(base.camera.getPos(render))
        if cluster == self.currentCluster:
            return task.cont

        # Hide everything first, then just show the PVS clusters.
        self.clusterNodes.hide()

        # If we had a previous cluster, remove its color and bin that indicates
        # it's the active one.
        if self.currentCluster != -1:
            self.clusterNodes[self.currentCluster].clearColor()
            self.clusterNodes[self.currentCluster].setBin('fixed', 0)

        if cluster != -1:
            self.clusterNodes[cluster].setColor((1, 0, 0, 1), 1)
            self.clusterNodes[cluster].setBin('fixed', 1)

        self.currentCluster = cluster

        if cluster == -1:
            return task.cont

        # Show ourselves and the visible clusters.
        pvs = self.lvlData.getClusterPvs(cluster)
        self.clusterNodes[cluster].show()
        for i in range(pvs.getNumVisibleClusters()):
            self.clusterNodes[pvs.getVisibleCluster(i)].show()

        return task.cont

    def visDebugEnable(self):
        # Make sure we've loaded the debug geometry for each visgroup.
        if not self.loadedVisBoxes:
            self.loadVisDebugGeometry()

        base.taskMgr.add(self.updateVisDebug, 'visDebug', sort=48)

    def visDebugDisable(self):
        if self.clusterNodes:
            self.clusterNodes.hide()
        base.taskMgr.remove('visDebug')

    def loadVisDebugGeometry(self):
        self.loadedVisBoxes = True
        self.clusterNodes = NodePathCollection()
        for i in range(self.lvlData.getNumClusters()):
            clusterData = self.lvlData.getClusterPvs(i)
            lines = LineSegs('cluster-' + str(i))
            lines.setColor(ClusterColors[i % len(ClusterColors)])
            for j in range(clusterData.getNumBoxes()):
                mins = LPoint3()
                maxs = LPoint3()
                clusterData.getBoxBounds(j, mins, maxs)
                lines.move_to(mins)
                lines.draw_to(LPoint3(mins.get_x(), mins.get_y(), maxs.get_z()))
                lines.draw_to(LPoint3(mins.get_x(), maxs.get_y(), maxs.get_z()))
                lines.draw_to(LPoint3(mins.get_x(), maxs.get_y(), mins.get_z()))
                lines.draw_to(mins)
                lines.draw_to(LPoint3(maxs.get_x(), mins.get_y(), mins.get_z()))
                lines.draw_to(LPoint3(maxs.get_x(), mins.get_y(), maxs.get_z()))
                lines.draw_to(LPoint3(mins.get_x(), mins.get_y(), maxs.get_z()))
                lines.move_to(LPoint3(maxs.get_x(), mins.get_y(), maxs.get_z()))
                lines.draw_to(maxs)
                lines.draw_to(LPoint3(mins.get_x(), maxs.get_y(), maxs.get_z()))
                lines.move_to(maxs)
                lines.draw_to(LPoint3(maxs.get_x(), maxs.get_y(), mins.get_z()))
                lines.draw_to(LPoint3(mins.get_x(), maxs.get_y(), mins.get_z()))
                lines.move_to(LPoint3(maxs.get_x(), maxs.get_y(), mins.get_z()))
                lines.draw_to(LPoint3(maxs.get_x(), mins.get_y(), mins.get_z()))
            np = self.lvl.attachNewNode(lines.create())
            np.setDepthWrite(False)
            np.setDepthTest(False)
            np.setBin('fixed', 0)
            self.clusterNodes.addPath(np)

    def worldLoaded(self):
        """
        Called by the world when its DO has been generated.  We can now load
        the level and notify the server we have joined the game.
        """
        self.changeLevel(self.levelName)
        self.sendUpdate("joinGame", ['Brian'])

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        base.game = self

    def unloadLevel(self):
        DistributedGameBase.unloadLevel(self)
        base.dynRender.node().levelShutdown()

    def changeLevel(self, lvlName):
        DistributedGameBase.changeLevel(self, lvlName)

        # Initialize the dynamic vis node to the number of visgroups in the
        # new level.
        base.dynRender.node().levelInit(self.lvlData.getNumClusters())

        # Here we build up the scene graph visibility info from the map vis
        # info for culling scene graph nodes.

        sceneTop = MapRender("top")
        sceneTop.replaceNode(base.render.node())
        sceneTop.setMapData(self.lvlData)

        # We need an idential MapRender for the top node of the viewmodel
        # scene graph.  Allows MapLightingEffect to work on viewmodels.
        vmTop = MapRender("vmTop")
        vmTop.replaceNode(base.vmRender.node())
        vmTop.setMapData(self.lvlData)

        render.setAttrib(LightRampAttrib.makeHdr0())

        # Check for a fog controller.
        for i in range(self.lvlData.getNumEntities()):
            ent = self.lvlData.getEntity(i)
            if ent.getClassName() != "env_fog_controller":
                continue

            self.fogMgr = FogManager()
            props = ent.getProperties()

            if props.hasAttribute("fogstart"):
                self.fogMgr.fogStart = props.getAttributeValue("fogstart").getFloat()
            if props.hasAttribute("fogend"):
                self.fogMgr.fogEnd = props.getAttributeValue("fogend").getFloat()
            if props.hasAttribute("fogdir"):
                props.getAttributeValue("fogdir").toVec3(self.fogMgr.fogDir)
                self.fogMgr.fogDir.normalize()
            if props.hasAttribute("fogblend"):
                self.fogMgr.fogBlend = props.getAttributeValue("fogblend").getBool()
            if props.hasAttribute("fogcolor"):
                str_rgb = props.getAttributeValue("fogcolor").getString().split()
                self.fogMgr.color[0] = pow(float(str_rgb[0]) / 255.0, 2.2)
                self.fogMgr.color[1] = pow(float(str_rgb[1]) / 255.0, 2.2)
                self.fogMgr.color[2] = pow(float(str_rgb[2]) / 255.0, 2.2)
            if props.hasAttribute("fogcolor2"):
                str_rgb = props.getAttributeValue("fogcolor2").getString().split()
                self.fogMgr.color2[0] = pow(float(str_rgb[0]) / 255.0, 2.2)
                self.fogMgr.color2[1] = pow(float(str_rgb[1]) / 255.0, 2.2)
                self.fogMgr.color2[2] = pow(float(str_rgb[2]) / 255.0, 2.2)
            if props.hasAttribute("fogenable"):
                if props.getAttributeValue("fogenable").getBool():
                    #print("enable")
                    self.fogMgr.enableFog()

            break

    def delete(self):
        del base.game
        DistributedObject.delete(self)
        DistributedGameBase.delete(self)

    def emitSound(self, soundIndex, waveIndex, volume, pitch, origin):
        sound = Sounds.createSoundClient(soundIndex, waveIndex, volume, pitch, origin)
        if sound:
            play_sound_coll.start()
            sound.play()
            play_sound_coll.stop()

    def doExplosion(self, pos, scale):
        root = base.dynRender.attachNewNode("expl")
        root.setEffect(MapLightingEffect.make())
        root.setPos(Vec3(*pos))
        root.setScale(Vec3(*scale))
        expl = base.loader.loadModel("models/effects/explosion")
        expl.setZ(8)
        expl.hide(DirectRender.ShadowCameraBitmask)
        seqn = expl.find("**/+SequenceNode").node()
        seqn.play()
        expl.reparentTo(root)
        expl.setBillboardPointEye()
        seq = Sequence(Wait(seqn.getNumFrames() / seqn.getFrameRate()), Func(root.removeNode))
        seq.start()

    def doTracer(self, start, end):
        #print("tracer", start, end)
        start = Point3(start[0], start[1], start[2])
        end = Point3(end[0], end[1], end[2])
        speed = 5000
        color = Vec4(1.0, 0.85, 0.5, 1)
        traceDir = end - start
        traceLen = traceDir.length()
        traceDir /= traceLen
        length = traceLen / speed
        segs = LineSegs('segs')
        segs.setColor(color)
        segs.moveTo(Point3(0))
        segs.drawTo(Vec3(0, -1, 0))
        segs.setThickness(2)
        np = base.dynRender.attachNewNode(segs.create())
        np.setLightOff(1)
        np.lookAt(traceDir)
        np.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OOne, ColorBlendAttrib.OOne), 1)
        segs.setVertexColor(1, Vec4(0.0))

        seq = Sequence()

        p1 = Parallel()
        p1.append(LerpPosInterval(np, length, end, start))
        p1.append(LerpScaleInterval(np, length, (1, traceLen, 1), (1, 0.01, 1)))
        p2 = Parallel()
        p2.append(LerpScaleInterval(np, length, (1, 0.01, 1), (1, traceLen, 1)))

        seq.append(p1)
        seq.append(p2)
        seq.append(Func(np.removeNode))

        seq.start()

    def doTracers(self, origin, ends):
        for i in range(len(ends)):
            self.doTracer(origin, ends[i])



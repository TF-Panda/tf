""" DistributedGame module: contains the DistributedGame class """

from direct.distributed2.DistributedObject import DistributedObject
from direct.directbase import DirectRender

from panda3d.core import *
from panda3d.pphysics import *

from direct.gui.DirectGui import OnscreenText

from direct.interval.IntervalGlobal import Sequence, Wait, Func, Parallel, LerpPosInterval, LerpScaleInterval

from tf.tfbase import Sounds, TFLocalizer

from .DistributedGameBase import DistributedGameBase
from .FogManager import FogManager
from .SkyBox import SkyBox
from tf.tfbase.Soundscapes import SoundscapeManager

from .CubemapRendering import CubemapRendering

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

        self.roundNumber = 0
        self.roundTimeRemaining = 0
        self.roundState = 0

        self.roundTimeText = OnscreenText("", pos=(0, 0.85), fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1), align=TextNode.ACenter)

        self.ssMgr = SoundscapeManager()

        self.sky = None
        self.visDebug = False
        self.loadedVisBoxes = False
        self.clusterNodes = None
        self.currentCluster = -1
        self.fogMgr = None
        self.clnp = None
        self.waterGeomNp = None

        self.accept('shift-v', self.toggleVisDebug)
        self.accept('c', self.renderCubeMaps)

    def renderCubeMaps(self):
        print("Rendering cube maps...")
        r = CubemapRendering()
        r.renderCubemaps(self.lvlData)

    def RecvProxy_roundTimeRemaining(self, time):
        if time != self.roundTimeRemaining:
            self.roundTimeRemaining = time
            self.updateRoundTimer()

    def updateRoundTimer(self):
        minutes = self.roundTimeRemaining // 60
        seconds = self.roundTimeRemaining % 60

        self.roundTimeText.setText(str(minutes) + ":" + str(seconds).zfill(2))

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
        playerName = ConfigVariableString('tf-player-name', 'Player').value
        self.sendUpdate("joinGame", [playerName])

    def joinGameResp(self, tickCount):
        base.resetSimulation(tickCount)

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        base.game = self
        self.changeLevel(self.levelName)
        self.worldLoaded()

    def __updateCascadeLight(self, task):
        if not self.clnp:
            return task.done

        self.clnp.node().update(base.render)

        return task.cont

    def unloadLevel(self):
        DistributedGameBase.unloadLevel(self)

        if self.waterGeomNp:
            self.waterGeomNp.removeNode()
            self.waterGeomNp = None
            base.planarReflect.shutdown()
            base.planarRefract.shutdown()

        self.clnp = None
        base.taskMgr.remove('updateCascadeLight')

        self.ssMgr.destroySoundscapes()

        # Clear out 3-D skybox.
        base.sky3DRoot.node().removeAllChildren()

        base.dynRender.node().levelShutdown()
        if self.sky:
            self.sky.destroy()
            self.sky = None

    def preFlattenLevel(self):
        lvlData = self.lvlData
        lvlRoot = self.lvl.find("**/mapRoot")

        sky3dNodes = []
        # Extract 3-D skybox mesh groups.
        idx = lvlData.get3dSkyModelIndex()
        if idx != -1:
            sky3dNodes.append(NodePath(lvlData.getModel(idx).getGeomNode()))

        for np in sky3dNodes:
            if not lvlData.getDirLight().isEmpty():
                np.setLight(lvlData.getDirLight())
            np.reparentTo(base.sky3DRoot)

        skyCamera = None
        for i in range(lvlData.getNumEntities()):
            ent = lvlData.getEntity(i)
            if ent.getClassName() == "sky_camera":
                skyCamera = ent
                break
        if skyCamera is None:
            return

        props = skyCamera.getProperties()

        skyCamOrigin = Point3()
        props.getAttributeValue("origin").toVec3(skyCamOrigin)

        #skyCamAngles = Vec3()
        #if props.hasAttribute("use_angles") and props.getAttributeValue("use_angles").getBool():
        #    phr = Vec3()
        #    props.getAttributeValue("angles").toVec3(phr)
        #    skyCamAngles = Vec3(phr[1] - 90, -phr[0], phr[2])

        scale = 1.0 / 16.0
        if props.hasAttribute("scale"):
            scale = 1.0 / props.getAttributeValue("scale").getFloat()

        # Build skybox matrix.
        skyMat = LMatrix4.scaleMat((scale, scale, scale))
        skyMat.setRow(3, skyCamOrigin)
        skyMat.invertInPlace()
        base.sky3DRoot.setMat(skyMat)

        #base.sky3DMat = skyMat

        # Setup sky fog.
        """
        fogMgr = FogManager(base.sky3DRoot)

        if props.hasAttribute("fogstart"):
            fogMgr.fogStart = props.getAttributeValue("fogstart").getFloat()
        if props.hasAttribute("fogend"):
            fogMgr.fogEnd = props.getAttributeValue("fogend").getFloat()
        if props.hasAttribute("fogdir"):
            props.getAttributeValue("fogdir").toVec3(fogMgr.fogDir)
            fogMgr.fogDir.normalize()
        if props.hasAttribute("fogblend"):
            fogMgr.fogBlend = props.getAttributeValue("fogblend").getInt() == 1
        if props.hasAttribute("fogcolor"):
            str_rgb = props.getAttributeValue("fogcolor").getString().split()
            fogMgr.color[0] = pow(float(str_rgb[0]) / 255.0, 2.2)
            fogMgr.color[1] = pow(float(str_rgb[1]) / 255.0, 2.2)
            fogMgr.color[2] = pow(float(str_rgb[2]) / 255.0, 2.2)
        if props.hasAttribute("fogcolor2"):
            str_rgb = props.getAttributeValue("fogcolor2").getString().split()
            fogMgr.color2[0] = pow(float(str_rgb[0]) / 255.0, 2.2)
            fogMgr.color2[1] = pow(float(str_rgb[1]) / 255.0, 2.2)
            fogMgr.color2[2] = pow(float(str_rgb[2]) / 255.0, 2.2)
        if props.hasAttribute("fogenable"):
            if props.getAttributeValue("fogenable").getBool():
                fogMgr.enableFog()

        if props.hasAttribute("use_angles") and props.getAttributeValue("use_angles").getBool():
            # Use entity angles instead of fogdir property for directional
            # blend.
            phr = Vec3()
            props.getAttributeValue("angles").toVec3(phr)
            q = Quat()
            q.setHpr((phr[1] - 90, -phr[0], phr[2]))
            fogMgr.fogDir = q.getForward()

        self.skyFogMgr = fogMgr
        """

        #base.sky3DRoot.ls()
        #base.sky3DRoot.clearModelNodes()
        #self.flatten(base.sky3DRoot)
        #base.sky3DRoot.flattenStrong()

    def changeLevel(self, lvlName):
        DistributedGameBase.changeLevel(self, lvlName)

        #for i in range(self.lvlData.getNumAmbientProbes()):
        #    probe = self.lvlData.getAmbientProbe(i)
        #    print("Probe %i" % i)
        #    for j in range(9):
        #        print("\t%s" % repr(probe.getColor(j)))

        # Extract the skybox name.
        worldEnt = self.lvlData.getEntity(0)
        worldData = worldEnt.getProperties()
        skyName = "sky_upward_hdr"
        if worldData.hasAttribute("skyname"):
            skyName = worldData.getAttributeValue("skyname").getString()
            skyName += "_hdr"
        print("skyname:", skyName)
        self.sky = SkyBox(skyName)

        self.lvlData.setCam(base.cam)
        self.lvlData.buildTraceScene()
        base.sfxManagerList[0].setTraceScene(self.lvlData.getTraceScene())

        clnp = self.lvlData.getDirLight()
        if not clnp.isEmpty():
            cl = clnp.node()
            cl.setSceneCamera(base.cam)
            cl.setSoftnessFactor(1.0)
            cl.setShadowCaster(True, 2048, 2048)
            cl.setCameraMask(DirectRender.ShadowCameraBitmask)
            clnp.showThrough(DirectRender.ShadowCameraBitmask)
            clnp.reparentTo(base.cam)
            clnp.setCompass()
            base.taskMgr.add(self.__updateCascadeLight, 'updateCascadeLight', sort=49)
            self.clnp = clnp
        #base.csmDebug.setShaderInput("cascadeSampler", cl.getShadowMap())

        saData = self.lvlData.getSteamAudioSceneData()
        base.sfxManagerList[0].loadSteamAudioScene(saData.verts, saData.tris, saData.tri_materials, saData.materials)
        base.sfxManagerList[0].loadSteamAudioReflectionProbeBatch(self.lvlData.getSteamAudioProbeData())

        # Initialize the dynamic vis node to the number of visgroups in the
        # new level.
        base.dynRender.node().levelInit(self.lvlData.getNumClusters(), self.lvlData.getAreaClusterTree())

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

        #skyTop = MapRender("sky3DTop")
        #skyTop.replaceNode(base.sky3DTop.node())
        #skyTop.setMapData(self.lvlData)

        render.setAttrib(LightRampAttrib.makeHdr0())

        mdl = self.lvlData.getModel(0)
        gn = mdl.getGeomNode()
        waterGeomNode = GeomNode("water")
        for i in reversed(range(gn.getNumGeoms())):
            geom = gn.getGeom(i)
            state = gn.getGeomState(i)
            if state.hasAttrib(MaterialAttrib):
                mattr = state.getAttrib(MaterialAttrib)
                mat = mattr.getMaterial()
                if mat and isinstance(mat, SourceWaterMaterial):
                    gn.removeGeom(i)
                    waterGeomNode.addGeom(geom.makeCopy(), state)
        if waterGeomNode.getNumGeoms() > 0:
            geom = waterGeomNode.getGeom(0)
            reader = GeomVertexReader(geom.getVertexData(), "vertex")
            reader.setRow(geom.getPrimitive(0).getVertex(0))
            z = reader.getData3f().getZ()

            print("Water Z", z)
            print("Water GeomNode", waterGeomNode)

            waterGeomNp = base.render.attachNewNode(waterGeomNode)
            waterGeomNp.setShaderInput("u_fogLensNearFar", Vec2(base.camLens.getNear(), base.camLens.getFar()))
            print(base.camLens.getNear(), base.camLens.getFar())

            base.planarReflect.setup(Vec3(0, 0, 1), z)
            base.planarReflect.render(waterGeomNp)

            base.planarRefract.setup(Vec3(0, 0, -1), z)
            base.planarRefract.render(waterGeomNp)
            #base.planarRefract.debug()

            self.waterGeomNp = waterGeomNp

            del reader

        numSounds = 0
        sounds = [
            "/c/Users/brian/Desktop/Scott-joplin-maple-leaf-rag.mp3",
            "tfmodels/built_src/sound/ambient/computer_working.wav",
            "tfmodels/built_src/sound/ambient/computer_tape.wav",
            "tfmodels/built_src/sound/ambient/machines/wall_loop1.wav",
            "tfmodels/built_src/sound/ambient/engine_idle.wav",
            "tfmodels/built_src/sound/ambient/printer.wav"
        ]

        # Check for a fog controller.
        for i in range(self.lvlData.getNumEntities()):
            ent = self.lvlData.getEntity(i)

            if ent.getClassName() == "env_fog_controller":
                if not self.fogMgr:
                    self.fogMgr = FogManager(base.render)
                    props = ent.getProperties()

                    if props.hasAttribute("fogstart"):
                        self.fogMgr.fogStart = props.getAttributeValue("fogstart").getFloat()
                    if props.hasAttribute("fogend"):
                        self.fogMgr.fogEnd = props.getAttributeValue("fogend").getFloat()
                    if props.hasAttribute("fogdir"):
                        props.getAttributeValue("fogdir").toVec3(self.fogMgr.fogDir)
                        self.fogMgr.fogDir.normalize()
                    if props.hasAttribute("fogblend"):
                        self.fogMgr.fogBlend = props.getAttributeValue("fogblend").getInt() == 1
                    if props.hasAttribute("fogcolor"):
                        str_rgb = props.getAttributeValue("fogcolor").getString().split()
                        self.fogMgr.color[0] = float(str_rgb[0]) / 255.0
                        self.fogMgr.color[1] = float(str_rgb[1]) / 255.0
                        self.fogMgr.color[2] = float(str_rgb[2]) / 255.0
                    if props.hasAttribute("fogcolor2"):
                        str_rgb = props.getAttributeValue("fogcolor2").getString().split()
                        self.fogMgr.color2[0] = float(str_rgb[0]) / 255.0
                        self.fogMgr.color2[1] = float(str_rgb[1]) / 255.0
                        self.fogMgr.color2[2] = float(str_rgb[2]) / 255.0
                    if props.hasAttribute("fogenable"):
                        if props.getAttributeValue("fogenable").getInt() == 1:
                            #print("enable")
                            self.fogMgr.updateParams()
                            self.fogMgr.enableFog()
                            #pass

        # Load up soundscapes.
        self.ssMgr.createSoundscapesFromLevel(self.lvlData)
        self.ssMgr.start()

        # Enable Z-prepass on the static brush geometry for the main pass.
        geomNp = self.lvl.find("**/mapRoot")
        geomNp.showThrough(DirectRender.ShadowCameraBitmask)
        #geomNp.setAttrib(DepthPrepassAttrib.make(DirectRender.MainCameraBitmask))

        #self.lvl.ls()
        #self.lvl.analyze()

        # Ensure all graphics objects are prepared ahead of time.

        # The models aren't parented to render yet since they are tied to
        # DistributedEntities that haven't been generated yet... so prepare
        # them explicitly.
        for i in range(self.lvlData.getNumModels()):
            mdl = self.lvlData.getModel(i)
            NodePath.anyPath(mdl.getGeomNode()).prepareScene(base.win.getGsg())

        base.render.prepareScene(base.win.getGsg())

        self.flatten(base.sky3DRoot)
        base.sky3DRoot.prepareScene(base.win.getGsg())

        # Render a few frames to flush the pipeline, that way all of our
        # queued textures, vbuffers, etc, are fully uploaded before we do
        # anything else.  Even without the multithreaded pipeline we want
        # to do this to get all of our uploads out of the way right now.
        base.graphicsEngine.renderFrame()
        base.graphicsEngine.renderFrame()

    def getTeamFormat(self, team):
        if team == 0:
            return "\1redteam\1"
        else:
            return "\1blueteam\1"

    def killEvent(self, killerDoId, assistDoId, weaponDoId, killedDoId):
        if not hasattr(base, 'localAvatar'):
            return

        killer = base.cr.doId2do.get(killerDoId)
        assist = base.cr.doId2do.get(assistDoId)
        weapon = base.cr.doId2do.get(weaponDoId)
        killed = base.cr.doId2do.get(killedDoId)

        suicide = killer is not None and killed is not None and killer == killed

        priority = killer == base.localAvatar or assist == base.localAvatar or killed == base.localAvatar
        if suicide:
            # Someone killed themselves.
            if assist:
                text = self.getTeamFormat(assist.team) + killer.playerName + TFLocalizer.PlayerKilled + self.getTeamFormat(killed.team) + killed.playerName + "\2"
            else:
                text = self.getTeamFormat(killed.team) + killed.playerName + TFLocalizer.PlayerSwitchTeam
        elif killer == base.world:
            text = self.getTeamFormat(killed.team) + killed.playerName + TFLocalizer.PlayerKillHealth
        else:
            # Someone killed someone else.
            text = ""
            if killer.isObject():
                text += self.getTeamFormat(killer.team) + killer.objectName
                builder = base.cr.doId2do.get(killer.builderDoId)
                if builder:
                    if builder == base.localAvatar:
                        priority = True
                    text += " (" + builder.playerName + ")"
                text += "\2"
            else:
                text += self.getTeamFormat(killer.team) + killer.playerName + "\2"
                if assist:
                    text += " + " + self.getTeamFormat(assist.team) + assist.playerName + "\2"
            text += TFLocalizer.PlayerKilled
            if killed.isObject():
                text += self.getTeamFormat(killed.team) + killed.objectName
                builder = base.cr.doId2do.get(killed.builderDoId)
                if builder:
                    if builder == base.localAvatar:
                        priority = True
                    text += " (" + builder.playerName + ")"
                text += "\2"
            else:
                text += self.getTeamFormat(killed.team) + killed.playerName + "\2"

        base.localAvatar.killFeed.pushEvent(text, priority)

    def teamFormattedString(self, team, string):
        return self.getTeamFormat(team) + string + "\2"

    def domEvent(self, a, b):
        """
        A is dominating B.
        """

        plyrA = base.cr.doId2do.get(a)
        if not plyrA:
            return
        plyrB = base.cr.doId2do.get(b)
        if not plyrB:
            return

        priority = base.localAvatar in (plyrA, plyrB)
        text = TFLocalizer.PlayerIsDominating % (self.teamFormattedString(plyrA.team, plyrA.playerName),
                                                 self.teamFormattedString(plyrB.team, plyrB.playerName))
        base.localAvatar.killFeed.pushEvent(text, priority)

    def revengeEvent(self, a, b):
        """
        A got revenge on B.
        """
        plyrA = base.cr.doId2do.get(a)
        if not plyrA:
            return
        plyrB = base.cr.doId2do.get(b)
        if not plyrB:
            return

        priority = base.localAvatar in (plyrA, plyrB)
        text = TFLocalizer.PlayerGotRevenge % (self.teamFormattedString(plyrA.team, plyrA.playerName),
                                               self.teamFormattedString(plyrB.team, plyrB.playerName))
        base.localAvatar.killFeed.pushEvent(text, priority)

    def delete(self):
        del base.game
        DistributedObject.delete(self)
        DistributedGameBase.delete(self)

    def doExplosion(self, pos, scale):
        root = base.dynRender.attachNewNode("expl")
        root.setEffect(MapLightingEffect.make(DirectRender.MainCameraBitmask))
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

        tracerScale = min(64, traceLen)

        seq = Sequence()

        p1 = Parallel()
        p1.append(LerpPosInterval(np, length, end, start))
        p1.append(LerpScaleInterval(np, tracerScale / speed, (1, tracerScale, 1), (1, 0.01, 1)))
        p2 = Parallel()
        p2.append(LerpScaleInterval(np, tracerScale / speed, (1, 0.01, 1), (1, tracerScale, 1)))

        seq.append(p1)
        seq.append(p2)
        seq.append(Func(np.removeNode))

        seq.start()

        from tf.weapon import WeaponEffects
        WeaponEffects.tracerSound(start, end)

    def doTracers(self, origin, ends):
        if base.cr.prediction.inPrediction:
            saveFrameTime = float(base.frameTime)
            base.setFrameTime(base.getRenderTime())

        for i in range(len(ends)):
            self.doTracer(origin, ends[i])

        if base.cr.prediction.inPrediction:
            base.setFrameTime(saveFrameTime)

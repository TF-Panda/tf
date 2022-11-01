"""Soundscapes module: contains the Soundscapes class."""

from panda3d.core import *

from .Sounds import attenToDistMult

from tf.tfbase import TFGlobals

import random

class SoundscapeComponentDef:

    def __init__(self):
        self.pitch = [1.0, 1.0]
        self.volume = [1.0, 1.0]
        self.distMult = 1.0
        self.position = -1
        self.looping = False
        self.intervalMin = 0.0
        self.intervalMax = 0.0
        self.waveFilenames = []

class SoundscapeDef:

    def __init__(self):
        self.name = ""
        self.components = []

Soundscapes = {}

def loadSoundscapeFile(filename):
    print("Reading soundscape file %s" % filename.getFullpath())

    kv = KeyValues.load(filename)
    if not kv:
        return False

    for i in range(kv.getNumChildren()):
        scape = kv.getChild(i)

        ss = SoundscapeDef()
        ss.name = scape.getName()

        for j in range(scape.getNumChildren()):
            child = scape.getChild(j)
            childName = child.getName()

            if childName == "playlooping" or childName == "playrandom":
                comp = SoundscapeComponentDef()

                if childName == "playlooping":
                    comp.looping = True

                for k in range(child.getNumKeys()):
                    key = child.getKey(k)
                    value = child.getValue(k)

                    if key == "pitch":
                        if "," in value:
                            strPitchRange = value.split(",")
                            comp.pitch = [float(strPitchRange[0]), float(strPitchRange[1])]
                        else:
                            comp.pitch = [float(value), float(value)]
                    elif key == "volume":
                        if "," in value:
                            strVolRange = value.split(",")
                            comp.volume = [float(strVolRange[0]), float(strVolRange[1])]
                        else:
                            comp.volume = [float(value), float(value)]
                    elif key == "attenuation":
                        comp.distMult = attenToDistMult(float(value))
                    elif key == "position":
                        comp.position = float(value)
                    elif key == "wave":
                        comp.waveFilenames = [Filename.fromOsSpecific(value)]
                    elif key == "time":
                        if "," in value:
                            strTimeRange = value.split(",")
                            comp.intervalMin = float(strTimeRange[0])
                            comp.intervalMax = float(strTimeRange[1])
                        else:
                            comp.intervalMin = float(value)
                            comp.intervalMax = float(value)

                if childName == "playrandom":
                    for k in range(child.getNumChildren()):
                        compChild = child.getChild(k)

                        if compChild.getName() == "rndwave":
                            for l in range(compChild.getNumKeys()):
                                if compChild.getKey(l) == "wave":
                                    comp.waveFilenames.append(Filename.fromOsSpecific(compChild.getValue(l)))

                ss.components.append(comp)

        Soundscapes[ss.name] = ss

    return True

def loadSoundscapes():
    filename = Filename("scripts/soundscapes_manifest.txt")
    kv = KeyValues.load(filename)
    if not kv:
        return False

    block = kv.getChild(0)

    for i in range(block.getNumKeys()):
        key = block.getKey(i)
        if key == "file":
            ssFilename = Filename.fromOsSpecific(block.getValue(i))
            loadSoundscapeFile(ssFilename)

    return True

class SoundscapeComponent:

    def __init__(self, soundscape, desc):
        self.soundscape = soundscape
        self.desc = desc
        self.sound = None
        self.soundVolume = 1.0
        self.task = None

    def preloadSounds(self):
        for fname in self.desc.waveFilenames:
            base.loader.loadSfx(fname)

    def update(self):
        if self.sound:
            self.sound.setVolume(self.soundscape.volume * self.soundVolume)

    def start(self):
        if len(self.desc.waveFilenames) > 1 or self.desc.intervalMin != self.desc.intervalMax:
            # We have multiple sound filenames, so play them randomly each
            # interval.
            delay = random.uniform(self.desc.intervalMin, self.desc.intervalMax)
            self.task = base.taskMgr.doMethodLater(delay, self.__playSoundTask, 'ssCompPlay')
        else:
            # Otherwise, just play the single sound.
            self.playSound()

    def playSound(self):
        if self.sound:
            self.sound.stop()
            self.sound = None

        filename = random.choice(self.desc.waveFilenames)
        volume = random.uniform(self.desc.volume[0], self.desc.volume[1])
        self.soundVolume = volume
        # Stream it if we're looping.
        # Actually, don't stream, opening the stream causes a chug.
        # Should look into non-blocking reads.
        self.sound = base.loader.loadSfx(filename)#, stream=self.desc.looping)
        self.sound.setLoop(self.desc.looping)
        self.sound.setVolume(self.soundscape.volume * volume)

        if self.desc.position != -1:
            # This is a spatialized soundscape component.
            sprops = SteamAudioProperties()
            #sprops._enable_air_absorption = False
            #sprops._enable_distance_atten = True
            #sprops._enable_air_absorption = False
            #sprops._enable_directivity = False
            #sprops._enable_occlusion = True
            #sprops._enable_transmission = False
            #sprops._enable_reflections = False
            #sprops._enable_pathing = False
            #sprops._bilinear_hrtf = True
            #sprops._volumetric_occlusion = False
            self.sound.applySteamAudioProperties(sprops)

            pos = self.soundscape.positions[int(self.desc.position)]
            self.sound.set3dAttributes(pos, Quat.identQuat(), Vec3())
            self.sound.set3dMinDistance((1.0 / self.desc.distMult) if (self.desc.distMult > 0.0) else 1000000.0)

        self.sound.play()

    def __playSoundTask(self, task):
        self.playSound()
        task.delayTime = random.uniform(self.desc.intervalMin, self.desc.intervalMax)
        return task.again

    def stop(self):
        if self.sound:
            self.sound.stop()
            self.sound = None
        if self.task:
            self.task.remove()
            self.task = None

    def destroy(self):
        self.stop()
        self.soundscape = None
        self.desc = None
        self.soundVolume = None

class Soundscape:

    def __init__(self, desc):
        self.desc = desc
        self.positions = []
        for i in range(8):
            self.positions.append(Point3(0))
        self.components = []
        self.volume = 0.0
        self.radius = -1
        self.task = None
        self.proxy = False
        self.fading = 0

        self.position = Point3()

        for compDesc in desc.components:
            comp = SoundscapeComponent(self, compDesc)
            comp.preloadSounds()
            self.components.append(comp)

    @staticmethod
    def createFromLevelEntity(lvlData, props):

        def findEntityByTargetName(targetName):
            for i in range(lvlData.getNumEntities()):
                ent = lvlData.getEntity(i)
                props = ent.getProperties()
                if props.hasAttribute("targetname") and props.getAttributeValue("targetname").getString() == targetName:
                    return ent
            return None

        if props.hasAttribute("targetname"):
            ssTargetName = props.getAttributeValue("targetname").getString()
        else:
            ssTargetName = ""

        soundscapeName = props.getAttributeValue("soundscape").getString()
        desc = Soundscapes.get(soundscapeName)
        if desc is None:
            print("env_soundscape %s specified non-existent soundscape %s" % (ssTargetName, soundscapeName))
            return None

        ss = Soundscape(desc)

        props.getAttributeValue("origin").toVec3(ss.position)
        ss.radius = props.getAttributeValue("radius").getFloat()

        # Fill out positions list for spatialized components.
        for i in range(props.getNumAttributes()):
            name = props.getAttributeName(i)
            if "position" in name:
                index = int(name[8:])
                targetName = props.getAttributeValue(i).getString()
                # Grab the position from the info_target entity.
                ent = findEntityByTargetName(targetName)
                if not ent:
                    print("env_soundscape %s refers to non-existent position target %s" % (ssTargetName, targetName))
                else:
                    targetProps = ent.getProperties()
                    targetProps.getAttributeValue("origin").toVec3(ss.positions[index])

        return ss

    def start(self, fadeIn=False):
        if fadeIn:
            self.fading = 1
            # We don't set the volume to 0.0 because the soundscape
            # might be restarted during a fade out.
        else:
            self.volume = 1.0
            self.fading = 0

        # The soundscape might be started again while it's currently being faded
        # out and the task (and all components) are still active.
        if not self.task:
            for comp in self.components:
                comp.start()
            self.task = base.taskMgr.add(self.updateTask, 'updateSoundscape')

    def stop(self, fadeOut=False):
        if fadeOut:
            self.fading = 2
        else:
            self.fading = 0
            for comp in self.components:
                comp.stop()
            if self.task:
                self.task.remove()
                self.task = None

    def destroy(self):
        if self.components:
            for comp in self.components:
                comp.destroy()
        self.components = None
        if self.task:
            self.task.remove()
            self.task = None
        self.desc = None
        self.volume = None
        self.positions = None
        self.radius = None

    def updateTask(self, task):
        if self.fading == 1:
            # Fading in.
            self.volume = TFGlobals.approach(1.0, self.volume, 2.0 * globalClock.dt)
            if self.volume >= 1.0:
                # Fade in done.
                self.fading = 0
        elif self.fading == 2:
            # Fading out.
            self.volume = TFGlobals.approach(0.0, self.volume, 2.0 * globalClock.dt)
            if self.volume <= 0.0:
                # Fade out done, stop.
                self.stop(False)
                return task.done

        for comp in self.components:
            comp.update()
        return task.cont

class SoundscapeProxy:

    def __init__(self, actualSoundscape):
        self.actualSoundscape = actualSoundscape
        self.desc = self.actualSoundscape.desc
        self.radius = -1
        self.position = Point3(0)
        self.proxy = True

    def start(self, fadeIn=False):
        self.actualSoundscape.start(fadeIn)

    def stop(self, fadeOut=False):
        self.actualSoundscape.stop(fadeOut)

    def destroy(self):
        self.actualSoundscape = None
        self.desc = None
        self.radius = None
        self.position = None

class SoundscapeManager:
    """
    This class maintains all of the soundscapes in the level and determines
    the active soundscape for a given camera position.  It handles cross fading
    between soundscape transitions.
    """

    def __init__(self):
        self.soundscapes = []
        self.soundscapesByTargetName = {}
        self.currSoundscape = None
        self.task = None
        self.lastCamPos = Point3()

    def destroySoundscapes(self):
        self.stop()
        for ss in self.soundscapes:
            ss.destroy()
        self.soundscapes = []
        self.soundscapesByTargetName = {}
        self.currSoundscape = None

    def soundscapesEqual(self, a, b):
        if a is None or b is None:
            return a == b

        if a.proxy:
            if b.proxy:
                return a.actualSoundscape == b.actualSoundscape
            else:
                return a.actualSoundscape == b
        else:
            if b.proxy:
                return a == b.actualSoundscape
            else:
                return a == b

    def update(self, task):
        camPos = base.cam.getPos(base.render)

        if camPos == self.lastCamPos:
            return task.cont

        self.lastCamPos = camPos

        traceScene = base.game.lvlData.getTraceScene()

        # Sort soundscapes by distance to camera.
        sortedSoundscapes = list(self.soundscapes)
        sortedSoundscapes.sort(key = lambda ss: (ss.position - camPos).lengthSquared())

        # Eliminate soundscapes not in range.
        inRangeSoundscapes = [ss for ss in sortedSoundscapes if (ss.radius == -1) or ((ss.position - camPos).length() < ss.radius)]

        # Filter down to soundscapes that we have LOS to.
        visibleInRangeSoundscapes = [ss for ss in inRangeSoundscapes if not traceScene.traceLine(camPos, ss.position, BitMask32.allOn()).hasHit()]

        ss = self.currSoundscape
        if len(visibleInRangeSoundscapes) > 0:
            # If we have any visible in-range soundscapes, pick the closest one.
            ss = visibleInRangeSoundscapes[0]

        elif self.currSoundscape is None:
            if len(inRangeSoundscapes) > 0:
                ss = inRangeSoundscapes[0]
            elif len(sortedSoundscapes) > 0:
                ss = sortedSoundscapes[0]

        if not self.soundscapesEqual(ss, self.currSoundscape):
            if self.currSoundscape:
                self.currSoundscape.stop(True)
                self.currSoundscape = None
            if ss:
                self.currSoundscape = ss
                self.currSoundscape.start(True)
                #print("soundscape:", ss.desc.name, "proxy:", ss.proxy)

        return task.cont

    def start(self):
        self.task = base.taskMgr.add(self.update, 'soundscapeManagerUpdate')

    def stop(self):
        if self.task:
            self.task.remove()
            self.task = None

    def createSoundscapesFromLevel(self, lvlData):
        for i in range(lvlData.getNumEntities()):
            ent = lvlData.getEntity(i)
            if ent.getClassName() != "env_soundscape":
                continue

            props = ent.getProperties()
            targetName = ""
            if props.hasAttribute("targetname"):
                targetName = props.getAttributeValue("targetname").getString()
            ss = Soundscape.createFromLevelEntity(lvlData, props)
            if ss is not None:
                self.soundscapes.append(ss)
                self.soundscapesByTargetName[targetName] = ss

        # Now load up the proxies.
        for i in range(lvlData.getNumEntities()):
            ent = lvlData.getEntity(i)
            if ent.getClassName() != "env_soundscape_proxy":
                continue

            props = ent.getProperties()

            actualSoundscapeName = props.getAttributeValue("MainSoundscapeName").getString()
            actualSoundscape = self.soundscapesByTargetName.get(actualSoundscapeName)
            if actualSoundscape:
                ss = SoundscapeProxy(actualSoundscape)
                ss.radius = props.getAttributeValue("radius").getFloat()
                props.getAttributeValue("origin").toVec3(ss.position)
                self.soundscapes.append(ss)
            else:
                print("env_soundscape_proxy refers to non-existent env_soundscape %s" % actualSoundscapeName)

        self.start()

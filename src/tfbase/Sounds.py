"""
Builds the sound list from the script file.
"""

import math
from enum import IntEnum
from panda3d.core import (
    ConfigVariableDouble, ConfigVariableList, Filename, KeyValues,
    PStatCollector, SteamAudioProperties, loadPrcFileData, ProxyAudioSound)
import random

from tf.tfbase import TFGlobals

csc_coll = PStatCollector("App:Sounds:CreateSoundClient")
get_sound_coll = PStatCollector("App:Sounds:CreateSoundClient:GetSound")

snd_refdb = ConfigVariableDouble("snd-refdb", 60.0)
snd_refdist = ConfigVariableDouble("snd-refdist", 36)

load_sounds = ConfigVariableList("load-sounds")

def attenToSoundLevel(attn):
    return ((50 + 20 / float(attn)) if attn else 0.0)

def soundLevelToAtten(sndlvl):
    return ((20.0 / float(sndlvl - 50)) if sndlvl > 50 else 4.0)

def attenToDistMult(attn):
    return soundLevelToDistMult(attenToSoundLevel(attn))

def soundLevelToDistMult(sndlvl):
    if sndlvl:
        return (math.pow(10.0, snd_refdb.value / 20) / math.pow(10.0, float(sndlvl) / 20)) / snd_refdist.value
    else:
        return 0.0

def distMultToSoundLevel(distMult):
    if distMult:
        return 20 * math.log10(math.pow(10.0, snd_refdb.value / 20) / (distMult * snd_refdist.value))
    else:
        return 0.0

def setSoundLevel(sound, sndlvl):
    sound.set3dMinDistance(1.0 / soundLevelToDistMult(sndlvl))

def sourcePitchToPlayRate(pitch):
    if pitch < 100:
        return TFGlobals.remapVal(pitch, 0, 100, 0.5, 1.0)
    elif pitch > 100:
        return TFGlobals.remapVal(pitch, 100, 255, 1.0, 2.0)
    else:
        return 1.0

class Channel(IntEnum):

    Invalid = -1

    CHAN_AUTO = 0
    CHAN_WEAPON = 1
    CHAN_VOICE = 2
    CHAN_ITEM = 3
    CHAN_BODY = 4
    CHAN_STREAM = 5
    CHAN_STATIC = 6
    CHAN_VOICE_BASE = 7
    CHAN_VOICE2 = 8

class SoundLevel(IntEnum):

    SNDLVL_NONE = 0
    SNDLVL_IDLE = 60
    SNDLVL_TALKING = 80
    SNDLVL_NORM = 75
    SNDLVL_STATIC = 66
    SNDLVL_GUNFIRE = 140

class Pitch(IntEnum):

    PITCH_LOW = 95
    PITCH_NORM = 100
    PITCH_HIGH = 120

class Wave:

    def __init__(self):
        self.filename = ""
        # Cached AudioSound data, None until first time wave is needed.
        self.sound = None
        self.spatialized = False
        self.loopStart = 0.0
        self.loopEnd = -1.0
        self.asyncHandle = None
        self.asyncProxies = []

    def __asyncCallback(self, sound):
        self.sound = sound
        self.sound.setLoopRange(self.loopStart, self.loopEnd)

        # Copy sound to each proxy.
        for proxy, mgr in self.asyncProxies:
            proxy.setRealSound(mgr.getSound(self.sound))
        self.asyncProxies = []

        self.asyncHandle = None

    def getSound(self, mgr):
        if self.asyncHandle:
            assert self.asyncProxies
            proxy = ProxyAudioSound(self.asyncProxies[0][0])
            self.asyncProxies.append((proxy, mgr))
            return proxy

        elif self.sound:
            return mgr.getSound(self.sound)

        else:
            proxy = ProxyAudioSound()
            proxy.setLoopRange(self.loopStart, self.loopEnd)
            self.asyncProxies = [(proxy, mgr)]
            self.asyncHandle = base.loader.loadSound(mgr, self.filename.getFullpath(),
                self.spatialized, self.__asyncCallback)
            return proxy

    def __repr__(self):
        return f"""
        Wave {self.filename}
          sound: {self.sound}
          spatialized: {self.spatialized}
        """

class SoundInfo:
    """
    Info about a single sound from the script file.
    """

    def __init__(self):
        # The name of it in the script file, for instance "Weapon_Wrench.Draw"
        self.name = ""
        # Volume range
        self.volume = [1.0, 1.0]
        # Pitch range.
        self.pitch = [1.0, 1.0]
        # The channel on the SoundEmitter that the sound plays on.
        # If not CHAN_STATIC or CHAN_AUTO, overrides the currently playing sound on that
        # channel.
        self.channel = Channel.CHAN_AUTO
        self.soundLevel = 0
        # This changes the spatial attenuation of the sound, comes from SNDLVL_X
        self.minDistance = 1.0
        self.distMult = 1.0
        self.wave = None
        # If there are multiple, we will randomly choose one.
        self.waves = []
        self.index = 0

    def __repr__(self):
        return f"""
        Sound {self.name}
          volume:     [{self.volume[0]}, {self.volume[1]}]
          channel:    {self.channel}
          soundLevel: {self.soundLevel}
          minDist:    {self.minDistance}
          wave:       {self.wave}
          distMult:   {self.distMult}
          waves       {self.waves}
        """

Sounds = {}
AllSounds = []

def createSound(info, spatial=False, getWave=False):
    if not info:
        return None

    wave = None
    if info.wave:
        wave = info.wave
    elif len(info.waves) > 0:
        wave = random.choice(info.waves)
    if not wave:
        return None

    sound = wave.getSound(base.sfxManager)
    sound.setPlayRate(random.uniform(info.pitch[0], info.pitch[1]))
    sound.setVolume(random.uniform(info.volume[0], info.volume[1]))
    if spatial:
        sound.set3dMinDistance(info.minDistance)
        props = SteamAudioProperties()
        props._enable_occlusion = True
        #props._enable_air_absorption = False
        sound.applySteamAudioProperties(props)
        #print(repr(info))

    if getWave:
        return (sound, wave)
    else:
        return sound

def createSoundByName(name, getInfo=False, spatial=False):
    info = Sounds.get(name, None)
    if not getInfo:
        return createSound(info, spatial)
    else:
        return (createSound(info, spatial), info)

def createSoundByIndex(index, getInfo=False, spatial=False):
    info = AllSounds[index]
    if not getInfo:
        return createSound(info, spatial)
    else:
        return (createSound(info, spatial), info)

def createSoundClient(index, waveIndex, volume, pitch, spatialized = False, getInfo=False):
    csc_coll.start()

    if index >= len(AllSounds):
        csc_coll.stop()
        if getInfo:
            return (None, None)
        return None

    info = AllSounds[index]
    if info.wave:
        wave = info.wave
    else:
        wave = info.waves[waveIndex]

    if not wave:
        csc_coll.stop()
        if getInfo:
            return (None, None)
        return None

    get_sound_coll.start()
    sound = wave.getSound(base.sfxManager)
    get_sound_coll.stop()
    sound.setPlayRate(pitch)
    sound.setVolume(volume)
    if spatialized:
        sound.set3dMinDistance(info.minDistance)
        props = SteamAudioProperties()
        props._enable_occlusion = True
        #props._enable_air_absorption = False
        sound.applySteamAudioProperties(props)
        #print(repr(info))

    csc_coll.stop()
    if getInfo:
        return (sound, info)
    return sound

def createSoundServer(name):
    info = Sounds.get(name, None)
    if not info:
        return None

    waveIdx = -1
    if info.wave:
        waveIdx = 0
    else:
        waveIdx = random.randint(0, len(info.waves) - 1)
    if waveIdx == -1:
        return None

    return [info.index, waveIdx, random.uniform(info.volume[0], info.volume[1]),
            random.uniform(info.pitch[0], info.pitch[1]), info.channel]

def processSound(kv):
    global Sounds

    info = SoundInfo()
    info.name = kv.getName()
    for i in range(kv.getNumKeys()):
        key = kv.getKey(i)
        value = kv.getValue(i)

        if key == "channel":
            info.channel = Channel[value]
        elif key == "volume":
            if value == "VOL_NORM":
                info.volume = [1.0, 1.0]
            else:
                minmax = "".join(value.split()).split(",")
                if len(minmax) > 1:
                    info.volume = [float(minmax[0]), float(minmax[1])]
                else:
                    info.volume = [float(minmax[0]), float(minmax[0])]
        elif key == "soundlevel":
            dbs = value.lower().split("sndlvl_")[1]
            if dbs.endswith("db"):
                info.soundLevel = int(dbs[:len(dbs) - 2])
            elif dbs.endswith("dbm"):
                # Fuckers.
                info.soundLevel = int(dbs[:len(dbs) - 3])
            else:
                info.soundLevel = SoundLevel[value]
            info.distMult = soundLevelToDistMult(info.soundLevel)
            if info.distMult > 0.0:
                info.minDistance = 1.0 / info.distMult
            else:
                info.minDistance = 1000000.0
        elif key == "wave":
            info.wave = Wave()
            if value.startswith(")") or value.startswith(">") or value.startswith("<"):
                info.wave.spatialized = True
                value = value[1:]
            elif value.startswith("#"):
                value = value[1:]
            info.wave.filename = Filename.fromOsSpecific(value.lower())
        elif key == "loopstart":
            assert info.wave
            info.wave.loopStart = float(value)
        elif key == "loopend":
            assert info.wave
            info.wave.loopEnd = float(value)
        elif key == "pitch":
            if value.upper() in Pitch.__members__:
                info.pitch = [Pitch[value.upper()], Pitch[value.upper()]]
            else:
                minmax = "".join(value.split()).split(",")
                if len(minmax) > 1:
                    info.pitch = [float(minmax[0]), float(minmax[1])]
                else:
                    info.pitch = [float(minmax[0]), float(minmax[0])]

            info.pitch[0] = sourcePitchToPlayRate(info.pitch[0])
            info.pitch[1] = sourcePitchToPlayRate(info.pitch[1])

    for i in range(kv.getNumChildren()):
        child = kv.getChild(i)
        if child.getName() == "rndwave":
            for j in range(child.getNumKeys()):
                value = child.getValue(j)
                wave = Wave()
                if value.startswith(")") or value.startswith(">") or value.startswith("<"):
                    wave.spatialized = True
                    value = value[1:]
                elif value.startswith("#"):
                    value = value[1:]
                wave.filename = Filename.fromOsSpecific(value.lower())
                info.waves.append(wave)

    info.index = len(AllSounds)
    Sounds[info.name] = info
    AllSounds.append(info)

def loadSounds(server = False):
    for i in range(load_sounds.getNumUniqueValues()):
        filename = Filename.fromOsSpecific(load_sounds.getUniqueValue(i))

        print("Loading sounds from %s" % filename.getFullpath())

        kv = KeyValues.load(filename)
        if not kv:
            print("Unable to load sound script file", filename)
            continue

        for j in range(kv.getNumChildren()):
            child = kv.getChild(j)
            processSound(child)

    #print(repr(Sounds))

def incRefDb():
    db = snd_refdb.value
    db += 1
    loadPrcFileData('', 'snd-refdb %s' % db)
    print("ref db:", db)

def decRefDb():
    db = snd_refdb.value
    db -= 1
    loadPrcFileData('', 'snd-refdb %s' % db)
    print("ref db:", db)

def enableRefDbDebug():
    base.accept('arrow_up', incRefDb)
    base.accept('arrow_down', decRefDb)

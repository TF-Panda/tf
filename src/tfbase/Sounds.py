"""
Builds the sound list from the script file.
"""

import math
from enum import IntEnum, auto
from panda3d.core import ConfigVariableDouble, ConfigVariableList, Filename, KeyValues, AudioManager, PitchShiftDSP, PStatCollector
import random

csc_coll = PStatCollector("App:Sounds:CreateSoundClient")
get_sound_coll = PStatCollector("App:Sounds:CreateSoundClient:GetSound")

snd_refdb = ConfigVariableDouble("snd-refdb", 60.0)
snd_refdist = ConfigVariableDouble("snd-refdist", 36)

load_sounds = ConfigVariableList("load-sounds")

def soundLevelToDistMult(sndlvl):
    if sndlvl:
        return (math.pow(10.0, snd_refdb.getValue() / 20) / math.pow(10.0, float(sndlvl) / 20)) / snd_refdist.getValue()
    else:
        return 0.0

def distMultToSoundLevel(distMult):
    if distMult:
        return 20 * math.log10(math.pow(10.0, snd_refdb.getValue() / 20) / (distMult * snd_refdist.getValue()))
    else:
        return 0.0

def remapVal(val, A, B, C, D):
    if A == B:
        return D if val >= B else C

    return C + (D - C) * (val - A) / (B - A)

class Channel(IntEnum):

    Invalid = -1

    CHAN_AUTO = auto()
    CHAN_WEAPON = auto()
    CHAN_VOICE = auto()
    CHAN_ITEM = auto()
    CHAN_BODY = auto()
    CHAN_STREAM = auto()
    CHAN_STATIC = auto()
    CHAN_VOICE_BASE = auto()
    CHAN_VOICE2 = auto()

class SoundLevel(IntEnum):

    SNDLVL_NONE = 0
    SNDLVL_IDLE = 60
    SNDLVL_TALKING = 60
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

    def getSound(self, mgr):
        if self.sound:
            return mgr.getSound(self.sound)
        else:
            self.sound = mgr.getSound(self.filename, self.spatialized)
            return self.sound

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
        # We interpret this as an index into base.sfxManagerList.
        self.channel = Channel.CHAN_AUTO
        self.soundLevel = 0
        # This changes the spatial attenuation of the sound, comes from SNDLVL_X
        self.minDistance = 1.0
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
          waves       {self.waves}
        """

Sounds = {}
AllSounds = []

def createSound(info):
    if not info:
        return None

    wave = None
    if info.wave:
        wave = info.wave
    elif len(info.waves) > 0:
        wave = random.choice(info.waves)
    if not wave:
        return None

    mgr = base.sfxManagerList[info.channel]
    sound = wave.getSound(mgr)
    if wave.spatialized:
        sound.set3dMinDistance(info.minDistance)
    sound.setPlayRate(random.uniform(info.pitch[0], info.pitch[1]))
    sound.setVolume(random.uniform(info.volume[0], info.volume[1]))

    return sound

def createSoundByName(name, getInfo=False):
    info = Sounds.get(name, None)
    if not getInfo:
        return createSound(info)
    else:
        return (createSound(info), info)

def createSoundByIndex(index, getInfo=False):
    info = AllSounds[index]
    if not getInfo:
        return createSound(info)
    else:
        return (createSound(info), info)

def createSoundClient(index, waveIndex, volume, pitch, pos):
    csc_coll.start()

    if index >= len(AllSounds):
        csc_coll.stop()
        return None

    info = AllSounds[index]
    if info.wave:
        wave = info.wave
    else:
        wave = info.waves[waveIndex]

    if not wave:
        csc_coll.stop()
        return None

    get_sound_coll.start()
    mgr = base.sfxManagerList[info.channel]
    sound = wave.getSound(mgr)
    get_sound_coll.stop()
    if wave.spatialized:
        sound.set3dMinDistance(info.minDistance)
    sound.setPlayRate(pitch)
    sound.setVolume(volume)
    sound.set3dAttributes(pos[0], pos[1], pos[2], 0, 0, 0)

    csc_coll.stop()
    return sound

def createSoundServer(name, pos):
    info = Sounds.get(name, None)
    if not info:
        return None

    waveIdx = -1
    if info.wave:
        waveIdx = 0
    else:
        waveIdx = random.choice(range(len(info.waves)))
    if waveIdx == -1:
        return None

    return [info.index, waveIdx, random.uniform(info.volume[0], info.volume[1]), random.uniform(info.pitch[0], info.pitch[1]), pos]

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
            info.minDistance = soundLevelToDistMult(info.soundLevel)
            if info.minDistance == 0:
                info.minDistance = 1
            else:
                info.minDistance = 1 / info.minDistance
        elif key == "wave":
            info.wave = Wave()
            if value.startswith(")"):
                info.wave.spatialized = True
                value = value[1:]
            info.wave.filename = Filename.fromOsSpecific(value.lower())
        elif key == "pitch":
            if value.upper() in Pitch.__members__:
                info.pitch = [Pitch[value.upper()], Pitch[value.upper()]]
            else:
                minmax = "".join(value.split()).split(",")
                if len(minmax) > 1:
                    info.pitch = [float(minmax[0]), float(minmax[1])]
                else:
                    info.pitch = [float(minmax[0]), float(minmax[0])]

            if info.pitch[0] < 100:
                info.pitch[0] = remapVal(info.pitch[0], 0, 100, 0.5, 1.0)
            elif info.pitch[0] > 100:
                info.pitch[0] = remapVal(info.pitch[0], 100, 255, 1.0, 2.0)
            else:
                info.pitch[0] = 1.0

            if info.pitch[1] < 100:
                info.pitch[1] = remapVal(info.pitch[1], 0, 100, 0.5, 1.0)
            elif info.pitch[1] > 100:
                info.pitch[1] = remapVal(info.pitch[1], 100, 255, 1.0, 2.0)
            else:
                info.pitch[1] = 1.0

    for i in range(kv.getNumChildren()):
        child = kv.getChild(i)
        if child.getName() == "rndwave":
            for j in range(child.getNumKeys()):
                value = child.getValue(i)
                wave = Wave()
                if value.startswith(")"):
                    wave.spatialized = True
                    value = value[1:]
                wave.filename = Filename.fromOsSpecific(value.lower())
                info.waves.append(wave)

    info.index = len(AllSounds)
    Sounds[info.name] = info
    AllSounds.append(info)

def loadSounds(server = False):
    if not server:
        for chan in Channel:
            # Create a new audio manager for each channel above the default
            # (which ShowBase creates automatically).
            if chan > 1:
                mgr = AudioManager.createAudioManager()
                base.addSfxManager(mgr)

        #for mgr in base.sfxManagerList:


    for i in range(load_sounds.getNumUniqueValues()):
        filename = Filename.fromOsSpecific(load_sounds.getUniqueValue(i))

        kv = KeyValues.load(filename)
        if not kv:
            print("Unable to load sound script file", filename)
            continue

        for j in range(kv.getNumChildren()):
            child = kv.getChild(j)
            processSound(child)

    #print(repr(Sounds))




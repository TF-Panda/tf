"""SoundEmitter module: contains the SoundEmitter class."""

from panda3d.core import PStatCollector, Quat, Vec3

from direct.showbase.DirectObject import DirectObject

buildListPColl = PStatCollector("SoundEmitter:BuildSpatialList")
updateAttributesPColl = PStatCollector("SoundEmitter:Update3DAttributes")

from .Sounds import Channel

# Set of channel ID's that allow more than one sound playing on the
# channel at a time.
NoOverrideChannels = (Channel.CHAN_STATIC, Channel.CHAN_AUTO)

class SoundData:
    pass

class SoundEmitter(DirectObject):
    """
    An object that emits spatialized and non-spatialized sounds from
    channels.

    A channel represents a particular category of sound that is emitted
    from the object.  Examples of channels might be voice (dialogue sounds),
    weapon, etc.

    Only one sound can play on a given channel at the same time.  If a new sound
    is played on a channel, the existing sound on that channel will be stopped.
    This eliminates the need to manually manage exclusive sounds, such character
    voice lines.
    """

    def __init__(self, host):
        # Dictionary of currently playing sound on each channel.
        self.chanSounds = {}
        # Separate list of sounds that don't play on any channel.  There is
        # no limit to the number of simultaneously playing general sounds.
        # Analagous to CHAN_STATIC/CHAN_AUTO.
        self.generalSounds = []

        self.spatialSounds = set()

        self.host = host
        self.task = None

        self.debug = False

    def stopAllSounds(self):
        self.stopSpatialTask()
        self.ignoreAll()
        for s in (self.generalSounds + list(self.chanSounds.values())):
            s.sound.stop()
        self.chanSounds = {}
        self.generalSounds = []
        self.spatialSounds = set()

    def stopChannel(self, chan):
        if chan < 0:
            self.stopAllSounds()

        elif chan in NoOverrideChannels:
            for s in self.generalSounds:
                self.ignore(s.eventName)
                s.sound.stop()
                if s in self.spatialSounds:
                    self.spatialSounds.remove(s)
            self.generalSounds = []

        elif chan in self.chanSounds:
            s = self.chanSounds[chan]
            self.ignore(s.eventName)
            s.sound.stop()
            del self.chanSounds[chan]
            if s in self.spatialSounds:
                self.spatialSounds.remove(s)

        if not self.spatialSounds:
            self.stopSpatialTask()

    def delete(self):
        self.stopAllSounds()
        self.chanSounds = None
        self.generalSounds = None
        self.spatialSounds = None
        self.host = None

    def __updateSpatialSounds(self, task):
        """
        Recomputes the 3-D position of all spatial sounds being emitted from
        this object based on the current spatial audio transform of the host.
        """

        #buildListPColl.start()
        #spatialSounds = [s for s in (self.generalSounds + list(self.chanSounds.values())) if s.spatial]
        #buildListPColl.stop()
        if not self.spatialSounds:
            return task.cont

        #updateAttributesPColl.start()

        center = self.host.getSpatialAudioCenter()
        # TODO: Should we check if the center changed since the last update?

        q = Quat.identQuat()
        v = Vec3()

        if self.debug:
            print("host center pos is", center.getRow3(3))

        for s in self.spatialSounds:
            pos = center.xformPoint(s.offset)
            if self.debug:
                print("set", s, "to pos", pos)
            s.sound.set3dAttributes(pos, q, v)

        #updateAttributesPColl.stop()

        return task.cont

    def registerSound(self, sound, channel, spatial=False, offset=(0, 0, 0)):
        """
        Registers the given AudioSound to be emitted from this object
        on the given channel.  If channel is None, the sound is not
        assigned to any channel and will not stop any existing sounds.
        """

        if channel in NoOverrideChannels:
            # This channel doesn't override sounds on the same channel.
            channel = None

        if channel is not None:
            # Sound is being played on a channel.  Stop existing sound on that
            # channel.
            soundData = self.chanSounds.get(channel)
            if soundData:
                # We can ignore the finished event for the sound since we're
                # about to override the reference anyways.
                self.ignore(soundData.eventName)
                soundData.sound.stop()
                if soundData in self.spatialSounds:
                    self.spatialSounds.remove(soundData)
                    if not self.spatialSounds:
                        self.stopSpatialTask()

        soundData = SoundData()
        soundData.sound = sound
        soundData.channel = channel
        soundData.spatial = spatial
        soundData.offset = offset
        if spatial:
            # Set up initial position for spatial sound immediately.
            # If we wait until next frame or later in this frame, the sound
            # may appear to jump.
            pos = self.host.getSpatialAudioCenter().xformPoint(offset)
            sound.set3dAttributes(pos, Quat.identQuat(), Vec3())
            self.spatialSounds.add(soundData)
            # Start the spatial update task if this is our first spatial sound.
            self.startSpatialTask()
        if channel is not None:
            self.chanSounds[channel] = soundData
        else:
            self.generalSounds.append(soundData)
        # Assign an event to the sound to handle when it is stopped
        # or plays to completion.
        soundData.eventName = "sound-" + str(id(sound)) + "-finished"
        sound.setFinishedEvent(soundData.eventName)
        self.acceptOnce(soundData.eventName, self.__handleSoundFinished, extraArgs=[soundData])

    def startSpatialTask(self):
        if not self.task:
            self.task = base.taskMgr.add(self.__updateSpatialSounds, "updateSpatialSounds", sort=49)

    def stopSpatialTask(self):
        if self.task:
            self.task.remove()
            self.task = None

    def __handleSoundFinished(self, soundData, sound):
        # Sound was stopped or played to completion.  Release
        # reference in our tables.

        if soundData.channel is not None:
            storedData = self.chanSounds.get(soundData.channel)
            if storedData == soundData:
                del self.chanSounds[soundData.channel]

        elif soundData in self.generalSounds:
            self.generalSounds.remove(soundData)

        if self.spatialSounds and soundData in self.spatialSounds:
            self.spatialSounds.remove(soundData)
            if not self.spatialSounds:
                # If we removed the last spatial sound, stop our update task.
                self.stopSpatialTask()

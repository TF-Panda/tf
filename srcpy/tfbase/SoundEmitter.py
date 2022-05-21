"""SoundEmitter module: contains the SoundEmitter class."""

from direct.showbase.DirectObject import DirectObject

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
        # Analagous to CHAN_STATIC.
        self.generalSounds = []

        self.host = host
        self.task = base.taskMgr.add(self.__updateSpatialSounds, "updateSpatialSounds", sort=49)

    def delete(self):
        self.task.remove()
        self.task = None
        self.ignoreAll()
        for s in (self.generalSounds + list(self.chanSounds.values())):
            s.sound.stop()
        self.chanSounds = None
        self.generalSounds = None
        self.host = None

    def __updateSpatialSounds(self, task):
        """
        Recomputes the 3-D position of all spatial sounds being emitted from
        this object based on the current spatial audio transform of the host.
        """

        spatialSounds = [s for s in (self.generalSounds + list(self.chanSounds.values())) if s.spatial]
        if not spatialSounds:
            return task.cont

        center = self.host.getSpatialAudioCenter()

        for s in spatialSounds:
            pos = center.xformPoint(s.offset)
            s.sound.set3dAttributes(pos.x, pos.y, pos.z, 0.0, 0.0, 0.0)

        return task.cont

    def registerSound(self, sound, channel, spatial=False, offset=(0, 0, 0)):
        """
        Registers the given AudioSound to be emitted from this object
        on the given channel.  If channel is None, the sound is not
        assigned to any channel and will not stop any existing sounds.
        """

        if channel is not None:
            # Sound is being played on a channel.  Stop existing sound on that
            # channel.
            soundData = self.chanSounds.get(channel)
            if soundData:
                # We can ignore the finished event for the sound since we're
                # about to override the reference anyways.
                self.ignore(soundData.eventName)
                soundData.sound.stop()

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
            sound.set3dAttributes(pos.x, pos.y, pos.z, 0.0, 0.0, 0.0)
        if channel is not None:
            self.chanSounds[channel] = soundData
        else:
            self.generalSounds.append(soundData)
        # Assign an event to the sound to handle when it is stopped
        # or plays to completion.
        soundData.eventName = "sound-" + str(id(sound)) + "-finished"
        sound.setFinishedEvent(soundData.eventName)
        self.acceptOnce(soundData.eventName, self.__handleSoundFinished, extraArgs=[soundData])

    def __handleSoundFinished(self, soundData, sound):
        # Sound was stopped or played to completion.  Release
        # reference in our tables.

        if soundData.channel is not None:
            storedData = self.chanSounds.get(soundData.channel)
            if storedData == soundData:
                del self.chanSounds[soundData.channel]

        elif soundData in self.generalSounds:
            self.generalSounds.remove(soundData)

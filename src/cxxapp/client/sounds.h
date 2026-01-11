#ifndef SOUNDS_H
#define SOUNDS_H

#include "pandabase.h"
#include "filename.h"
#include "audioSound.h"
#include "audioManager.h"
#include "audioEngine.h"
#include "pointerTo.h"
#include "randomizer.h"
#include "audioLoadRequest.h"
#include "proxyAudioSound.h"

class KeyValues;

// Sound manager.

/**
 * Loads sound definitions from the script files and allows getting an instance of a sound by name.
 */
class SoundManager {
public:
  enum SoundChannel {
    CHANNEL_invalid = -1,
    CHANNEL_auto = 0,
    CHANNEL_weapon,
    CHANNEL_voice,
    CHANNEL_item,
    CHANNEL_body,
    CHANNEL_stream,
    CHANNEL_static,
    CHANNEL_voice_base,
    CHANNEL_voice_2,
  };
  enum SoundLevel {
    SOUNDLEVEL_none,
    SOUNDLEVEL_idle = 60,
    SOUNDLEVEL_talking = 80,
    SOUNDLEVEL_norm = 75,
    SOUNDLEVEL_static = 66,
    SOUNDLEVEL_gunfire = 140,
  };
  enum Pitch {
    PITCH_invalid = -1,
    PITCH_low = 95,
    PITCH_norm = 100,
    PITCH_high = 120,
  };

  struct AsyncProxy {
    PT(ProxyAudioSound) proxy;
    AudioManager *mgr;
  };

  struct Wave {
    Filename filename;
    PT(AudioSound) sound;
    bool spatialized = false;
    float loop_start = 0.0f;
    float loop_end = -1.0f;
    PT(AudioLoadRequest) load_req;
    pvector<AsyncProxy> async_proxies;
  };

  struct SoundInfo : public ReferenceCount {
    int index = -1;
    std::string name;
    SoundChannel channel = CHANNEL_auto;
    float volume_min = 1.0f, volume_max = 1.0f;
    int soundlevel = SOUNDLEVEL_norm;
    float dist_mult = 1.0f;
    float min_dist = 1.0f;
    float pitch_min = 1.0f, pitch_max = 1.0f;

    // A sound can have multiple audio files that we randomly
    // pick from.
    typedef pvector<Wave> Waves;
    Waves waves;
  };

public:
  void initialize();

  void update();

  void load_sounds();
  void load_sound_script_file(const Filename &filename);

  void list_sounds() const;

  PT(AudioSound) create_sound(SoundInfo *info, bool spatial = false);
  PT(AudioSound) create_sound_by_name(const std::string &name, bool spatial = false);
  PT(AudioSound) get_wave_sound(Wave *wave, AudioManager *mgr);

  inline AudioManager *get_music_manager() const;
  inline AudioManager *get_sfx_manager() const;
  inline AudioEngine *get_engine() const;

  inline SoundInfo *get_sound_by_name(const std::string &name) const;
  inline int get_num_sounds() const;
  inline SoundInfo *get_sound(int n) const;

  inline static SoundManager *ptr();

private:
  void process_sound(KeyValues *sound_def);

private:
  typedef pvector<PT(SoundInfo)> SoundList;
  SoundList _sounds;
  typedef pflat_hash_map<std::string, PT(SoundInfo), string_hash> SoundsByName;
  SoundsByName _sounds_by_name;

  // Waves that are currently asynchronously loading
  // their sound data.
  pset<Wave *> _loading_waves;

  PT(AudioEngine) _audio_engine;
  PT(AudioManager) _music_manager;
  PT(AudioManager) _sfx_manager;

  Randomizer _random;

  static SoundManager *_global_ptr;
};

/**
 *
 */
inline AudioEngine *SoundManager::
get_engine() const {
  return _audio_engine;
}

/**
 *
 */
inline AudioManager *SoundManager::
get_music_manager() const {
  return _music_manager;
}

/**
 *
 */
inline AudioManager *SoundManager::
get_sfx_manager() const {
  return _sfx_manager;
}

/**
 *
 */
inline SoundManager::SoundInfo *SoundManager::
get_sound_by_name(const std::string &name) const {
  SoundsByName::const_iterator it = _sounds_by_name.find(name);
  if (it != _sounds_by_name.end()) {
    return (*it).second;
  }
  return nullptr;
}

/**
 *
 */
inline int SoundManager::
get_num_sounds() const {
  return (int)_sounds.size();
}

/**
 *
 */
inline SoundManager::SoundInfo *SoundManager::
get_sound(int n) const {
  nassertr(n >= 0 && n < get_num_sounds(), nullptr);
  return _sounds[n];
}

/**
 *
 */
inline SoundManager *SoundManager::
ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new SoundManager;
  }
  return _global_ptr;
}

#endif // SOUNDS_H

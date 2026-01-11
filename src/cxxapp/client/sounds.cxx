#include "sounds.h"
#include "audioManager.h"
#include "audioSound.h"
#include "config_audio.h"
#include "virtualFileSystem.h"
#include "configVariableList.h"
#include "keyValues.h"
#include "notifyCategoryProxy.h"
#include "string_utils.h"
#include "audioEngine.h"
#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstddef>
#include "nullAudioSound.h"
#include "steamAudioProperties.h"
#include "audioLoadRequest.h"
#include "loader.h"
#include "proxyAudioSound.h"

NotifyCategoryDeclNoExport(sounds);
NotifyCategoryDef(sounds, "tf");

static ConfigVariableList load_sounds_var
("load-sounds",
 PRC_DESC("Sounds script filenames to load at game start."));
static ConfigVariableDouble snd_refdb
("snd-refdb", 60.0,
 PRC_DESC("Reference db for calculating sound distance attenuation."));
static ConfigVariableDouble snd_refdist
("snd-refdist", 36);

static ConfigVariableDouble master_volume
("master-volume", 1.0f,
 PRC_DESC("Master game volume, both sfx and music."));
static ConfigVariableDouble sfx_volume
("sfx-volume", 1.0f,
 PRC_DESC("Volume of sound effects."));
static ConfigVariableDouble music_volume
("music-volume", 1.0f,
 PRC_DESC("Volume of music."));

SoundManager *SoundManager::_global_ptr = nullptr;

static PT(NullAudioSound) null_sound = new NullAudioSound;

/**
 *
 */
static SoundManager::SoundChannel
channel_from_script_name(const std::string &name) {
  if (name == "CHAN_AUTO") {
    return SoundManager::CHANNEL_auto;
  } else if (name == "CHAN_WEAPON") {
    return SoundManager::CHANNEL_weapon;
  } else if (name == "CHAN_VOICE") {
    return SoundManager::CHANNEL_voice;
  } else if (name == "CHAN_ITEM") {
    return SoundManager::CHANNEL_item;
  } else if (name == "CHAN_BODY") {
    return SoundManager::CHANNEL_body;
  } else if (name == "CHAN_STREAM") {
    return SoundManager::CHANNEL_stream;
  } else if (name == "CHAN_STATIC") {
    return SoundManager::CHANNEL_static;
  } else if (name == "CHAN_VOICE_BASE") {
    return SoundManager::CHANNEL_voice_base;
  } else if (name == "CHAN_VOICE2") {
    return SoundManager::CHANNEL_voice_2;
  } else {
    return SoundManager::CHANNEL_invalid;
  }
}

/**
 *
 */
static int
soundlevel_from_script_name(const std::string &name) {
  // Could be SNDLEVEL_TALKING, SNDLVL_55db, SNDLEVEL_65dbm.
  std::string dbs = downcase(name);
  // Get everything after the sndlvl_
  size_t sndlvl_pos = dbs.find("sndlvl_");
  if (sndlvl_pos == std::string::npos) {
    return SoundManager::SOUNDLEVEL_none;
  }
  dbs = dbs.substr(sndlvl_pos + 7);
  size_t len = dbs.length();
  if (dbs.length() > 2 && dbs.substr(dbs.length() - 2) == "db") {
    // SNDLVL_XXdb
    int ret;
    if (!string_to_int(dbs.substr(0, dbs.length() - 2), ret)) {
      return SoundManager::SOUNDLEVEL_none;
    }
    return ret;

  } else if (dbs.length() > 3 && dbs.substr(dbs.length() - 3) == "dbm") {
    // SNDLVL_XXdbm
    int ret;
    if (!string_to_int(dbs.substr(0, dbs.length() - 3), ret)) {
      return SoundManager::SOUNDLEVEL_none;
    }
    return ret;

  } else {
    // It's one of the named soundlevels.
    if (dbs == "none") {
      return SoundManager::SOUNDLEVEL_none;
    } else if (dbs == "idle") {
      return SoundManager::SOUNDLEVEL_idle;
    } else if (dbs == "talking") {
      return SoundManager::SOUNDLEVEL_talking;
    } else if (dbs == "norm") {
      return SoundManager::SOUNDLEVEL_norm;
    } else if (dbs == "static") {
      return SoundManager::SOUNDLEVEL_static;
    } else if (dbs == "gunfire") {
      return SoundManager::SOUNDLEVEL_gunfire;
    } else {
      return SoundManager::SOUNDLEVEL_none;
    }
  }
}

/**
 *
 */
static int
pitch_from_script_name(const std::string &value) {
  std::string lval = downcase(value);
  if (lval == "pitch_low") {
    return SoundManager::PITCH_low;
  } else if (lval == "pitch_norm") {
    return SoundManager::PITCH_norm;
  } else if (lval == "pitch_high") {
    return SoundManager::PITCH_high;
  } else {
    return SoundManager::PITCH_invalid;
  }
}

/**
 *
 */
static SoundManager::Wave
wave_from_script(const std::string &value) {
  SoundManager::Wave wv;
  std::string fname = downcase(value);
  if (!fname.empty() && (fname[0] == ')' || fname[0] == '>' || fname[0] == '<')) {
    wv.spatialized = true;
    fname = fname.substr(1);
  } else if (!fname.empty() && fname[0] == '#') {
    fname = fname.substr(1);
  }
  wv.filename = Filename::from_os_specific(fname);
  return wv;
}

/**
 *
 */
static float
soundlevel_to_dist_mult(int soundlevel) {
  if (soundlevel > 0) {
    return (powf(10.0f, (float)snd_refdb / 20.0f) / powf(10.0f, (float)soundlevel / 20.0f)) / (float)snd_refdist;
  } else {
    return 0.0f;
  }
}

/**
 *
 */
static int
dist_mult_to_soundlevel(float dist_mult) {
  if (dist_mult > 0.0f) {
    return 20 * log10f(powf(10.0f, (float)snd_refdb / 20.0f) / (dist_mult * (float)snd_refdist));
  } else {
    return SoundManager::SOUNDLEVEL_none;
  }
}

/**
 *
 */
static float
pitch_to_play_rate(float pitch) {
  return pitch * 0.01f;
}

/**
 *
 */
static float
db_to_gain(float db) {
  return powf(10.0f, db / 20.0f);
}

/**
 *
 */
static float
gain_to_db(float gain) {
  return 20.0f * logf(gain);
}

/**
 *
 */
static int
atten_to_soundlevel(float atten) {
  return atten > 0 ? ((50 + 20 / (float)atten)) : 0;
}

/**
 *
 */
static float
soundlevel_to_atten(int soundlevel) {
  return soundlevel > 50 ? (20.0f / (float)(soundlevel - 50)) : 4.0f;
}

/**
 *
 */
static std::string
remove_spaces(const std::string &str) {
  std::string trimmed = str;
  trimmed.erase(std::remove_if(trimmed.begin(), trimmed.end(), ::isspace), trimmed.end());
  return trimmed;
}

/**
 *
 */
void SoundManager::
initialize() {
  _audio_engine = AudioEngine::make_engine();

  // An audio manager is essentially a mixing group in a hierarchy.

  _music_manager = _audio_engine->make_manager("music");
  _music_manager->set_volume(music_volume * master_volume);
  // Allow only one song to play at a time.  We could also just manage this ourselves.
  _music_manager->set_concurrent_sound_limit(1);

  _sfx_manager = _audio_engine->make_manager("sfx");
  _sfx_manager->set_volume(sfx_volume * master_volume);
}

/**
 *
 */
void SoundManager::
update() {
  // Engine update automatically updates all managers.
  _audio_engine->update();

  // Check if any wave async loads finished.
  pvector<Wave *> done_waves;
  for (Wave *wv : _loading_waves) {
    assert(wv->load_req != nullptr);
    if (wv->load_req->is_ready()) {
      if (sounds_cat.is_debug()) {
	sounds_cat.debug()
	  << "Async load done for wave " << wv->filename << ", frame "
	  << ClockObject::get_global_clock()->get_frame_count() << "\n";
      }
      // Cool, the sound is ready.
      // Copy it to each proxy that got created during the load.
      wv->sound = wv->load_req->get_sound();
      wv->sound->set_loop_range(wv->loop_start, wv->loop_end);
      for (AsyncProxy &proxy : wv->async_proxies) {
	proxy.proxy->set_real_sound(proxy.mgr->get_sound(wv->sound));
      }
      wv->async_proxies.clear();
      wv->load_req = nullptr;
      done_waves.push_back(wv);
    }
  }
  // Now clear out the waves that finished from the loading list.
  for (Wave *wv : done_waves) {
    _loading_waves.erase(wv);
  }
}

/**
 * Loads all sound script files specified in the load-sounds config variable.
 */
void SoundManager::
load_sounds() {
  for (size_t i = 0; i < load_sounds_var.get_num_unique_values(); ++i) {
    const std::string &val = load_sounds_var.get_unique_value(i);
    Filename fname = Filename::from_os_specific(val);
    load_sound_script_file(fname);
  }
}

/**
 * Loads a single sound script file.
 */
void SoundManager::
load_sound_script_file(const Filename &filename) {
  PT(KeyValues) kv = KeyValues::load(filename);
  if (kv == nullptr) {
    sounds_cat.warning()
      << "Unable to load sound script file " << filename << "\n";
    return;
  }

  sounds_cat.info()
      << "Loading sounds from " << filename << "\n";

  for (size_t i = 0; i < kv->get_num_children(); ++i) {
    process_sound(kv->get_child(i));
  }
}

/**
 * Prints info about all loaded sounds to the console.
 */
void SoundManager::
list_sounds() const {
  sounds_cat.info()
    << "Num sounds: " << _sounds.size() << "\n";
  std::ostream &out = sounds_cat.info();
  for (SoundInfo *sound : _sounds) {
    out << "Sound " << sound->name << "\n";
    indent(out, 2) << "index " << sound->index << "\n";
    indent(out, 2) << "chan " << sound->channel << "\n";
    indent(out, 2) << "soundlevel " << sound->soundlevel << "\n";
    indent(out, 2) << "vol min " << sound->volume_min << "\n";
    indent(out, 2) << "vol max " << sound->volume_max << "\n";
    indent(out, 2) << "pitch min " << sound->pitch_min << "\n";
    indent(out, 2) << "pitch max " << sound->pitch_max << "\n";
    indent(out, 2) << "dist mult " << sound->dist_mult << "\n";
    indent(out, 2) << "min dist " << sound->min_dist << "\n";
    indent(out, 2) << sound->waves.size() << "waves\n";
    for (const Wave &wave : sound->waves) {
      indent(out, 2) << "Wave " << wave.filename << "\n";
      if (wave.sound == nullptr) {
	indent(out, 4) << "Sound data NOT loaded\n";
      } else {
	indent(out, 4) << "Sound data is loaded\n";
      }
      indent(out, 4) << "loop start " << wave.loop_start << "\n";
      indent(out, 4) << "loop end " << wave.loop_end << "\n";
      indent(out, 4) << "spatialized " << wave.spatialized << "\n";
    }
  }
}

/**
 * Creates a sound instance for the given SoundInfo.  The returned sound is
 * an actual audio sound that can be played etc.
 */
PT(AudioSound) SoundManager::
create_sound(SoundInfo *info, bool spatial) {
  if (info == nullptr) {
    return null_sound;
  }

  Wave *wv = nullptr;
  if (info->waves.size() > 1u) {
    // Pick a random wave.
    int wave_index = _random.random_int((int)info->waves.size());
    wv = &info->waves[wave_index];
  } else if (!info->waves.empty()) {
    wv = &info->waves[0];
  }

  if (wv == nullptr) {
    // Got no wave?
    return null_sound;
  }

  PT(AudioSound) sound = get_wave_sound(wv, _sfx_manager);
  // Set properties on the sound that were specified on the sound info.
  sound->set_play_rate(info->pitch_min + _random.random_real_unit() * (info->pitch_max - info->pitch_min));
  sound->set_volume(info->volume_min + _random.random_real_unit() * (info->volume_max - info->volume_min));
  if (spatial) {
    // Set up spatialization properties.
    sound->set_3d_min_distance(info->min_dist);
    SteamAudioProperties sprops;
    sprops._enable_occlusion = true;
    sprops._bilinear_hrtf = false;
    sound->apply_steam_audio_properties(sprops);
  }

  return sound;
}

/**
 *
 */
PT(AudioSound) SoundManager::
create_sound_by_name(const std::string &name, bool spatial) {
  SoundInfo *info = get_sound_by_name(name);
  if (info == nullptr) {
    return null_sound;
  }
  return create_sound(info, spatial);
}

/**
 *
 */
PT(AudioSound) SoundManager::
get_wave_sound(Wave *wave, AudioManager *mgr) {
  if (wave->load_req != nullptr) {
    // We should already have an existing proxy if the load request
    // is active.
    if (sounds_cat.is_debug()) {
      sounds_cat.debug()
	<< "New proxy during async load for wave " << wave->filename << "\n";
    }
    assert(!wave->async_proxies.empty());
    PT(ProxyAudioSound) proxy = new ProxyAudioSound(wave->async_proxies[0].proxy);
    // Keep track of this sound proxy.
    wave->async_proxies.push_back({ proxy, mgr });
    return proxy;

  } else if (wave->sound != nullptr) {
    // We've got a sound data already, make a new instance.
    if (sounds_cat.is_debug()) {
      sounds_cat.debug()
	<< "Create wave instance " << wave->filename << "\n";
    }
    return mgr->get_sound(wave->sound);

  } else {
    // We haven't loaded the sound yet, load the sound asychronously
    // and in the meantime give them a proxy sound.  When the real
    // sound comes in we can apply any properties they set on the
    // proxy sound to the real thing.
    if (sounds_cat.is_debug()) {
      sounds_cat.debug()
	<< "Starting async load of sound data for wave " << wave->filename
	<< ", frame " << ClockObject::get_global_clock()->get_frame_count() << "\n";;
    }
    wave->load_req = new AudioLoadRequest(mgr, wave->filename, wave->spatialized);
    Loader *loader = Loader::get_global_ptr();
    loader->load_async(wave->load_req);
    PT(ProxyAudioSound) proxy = new ProxyAudioSound;
    proxy->set_loop_range(wave->loop_start, wave->loop_end);
    wave->async_proxies.push_back({ proxy, mgr });
    // Keep track of this wave so we can check if the load finished in update().
    _loading_waves.insert(wave);
    return proxy;
  }
}

/**
 *
 */
void SoundManager::
process_sound(KeyValues *sound_def) {
  PT(SoundInfo) pinfo = new SoundInfo;

  SoundInfo &info = *pinfo;
  info.name = sound_def->get_name();

  for (size_t i = 0; i < sound_def->get_num_keys(); ++i) {
    const std::string &key = sound_def->get_key(i);
    const std::string &value = sound_def->get_value(i);

    if (key == "channel") {
      info.channel = channel_from_script_name(value);

    } else if (key == "volume") {
      if (value == "VOL_NORM") {
	info.volume_max = info.volume_min = 1.0f;
      } else {
	// Volume format: min,max
	vector_string words;
	std::string trimmed = remove_spaces(value);
	tokenize(trimmed, words, ",");
	if (words.size() == 1u) {
	  // Single volume.
	  if (!string_to_float(words[0], info.volume_min)) {
	    sounds_cat.error()
	      << "Couldn't parse volume " << words[0] << " to float\n";
	  } else {
	    info.volume_max = info.volume_min;
	  }
	} else if (words.size() > 1u) {
	  // Min and max volume, chosen randomly.
	  if (!string_to_float(words[0], info.volume_min)) {
	    sounds_cat.error()
	      << "Couldn't parse min volume " << words[0] << " to float\n";
	  }
	  if (!string_to_float(words[1], info.volume_max)) {
	    sounds_cat.error()
	      << "Couldn't parse max volume " << words[1] << " to float\n";
	    info.volume_max = info.volume_min;
	  }
	}
      }

    } else if (key == "soundlevel") {
      info.soundlevel = soundlevel_from_script_name(value);
      info.dist_mult = soundlevel_to_dist_mult(info.soundlevel);
      if (info.dist_mult > 0.0f) {
	info.min_dist = 1.0f / info.dist_mult;
      } else {
	info.min_dist = 1000000.0f;
      }

    } else if (key == "wave") {
      info.waves.push_back(wave_from_script(value));

    } else if (key == "loopstart") {
      assert(!info.waves.empty());
      string_to_float(value, info.waves[0].loop_start);

    } else if (key == "loopend") {
      assert(!info.waves.empty());
      string_to_float(value, info.waves[0].loop_end);

    } else if (key == "pitch") {
      int pitch = pitch_from_script_name(value);
      if (pitch == PITCH_invalid) {
	std::string trimmed = remove_spaces(value);
	vector_string words;
	tokenize(trimmed, words, ",");
	if (words.size() > 1u) {
	  string_to_float(words[0], info.pitch_min);
	  string_to_float(words[1], info.pitch_max);
	} else {
	  string_to_float(words[0], info.pitch_min);
	  info.pitch_max = info.pitch_min;
	}
      } else {
	info.pitch_min = info.pitch_min = pitch;
      }

      info.pitch_min = pitch_to_play_rate(info.pitch_min);
      info.pitch_max = pitch_to_play_rate(info.pitch_max);
    }
  }

  // Handle random wave block.
  for (size_t i = 0; i < sound_def->get_num_children(); ++i) {
    KeyValues *child = sound_def->get_child(i);
    if (child->get_name() == "rndwave") {
      for (size_t j = 0; j < child->get_num_keys(); ++j) {
	std::string value = child->get_value(j);
	info.waves.push_back(wave_from_script(value));
      }
    }
  }

  info.index = (int)_sounds.size();
  _sounds.push_back(pinfo);
  _sounds_by_name[info.name] = pinfo;
}

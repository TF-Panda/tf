//
// tf.prc.pp
//
// This file defines the script to auto-generate tf.prc at
// ppremake time.  This is intended to fill in some of the default
// parameters, in particular the default display types.
//

#output 50_tf.prc notouch
#### Generated automatically by $[PPREMAKE] $[PPREMAKE_VERSION] from $[notdir $[THISFILENAME]].
################################# DO NOT EDIT ###########################

#if $[CTPROJS]
// If we are using the ctattach tools, append "built"--this is a VR
// Studio convention.
model-path      $TFMODELS/built
model-path      $TFMODELS/built/sound
sound-path      $TFMODELS/built
#else
// Most people outside the VR Studio just see this.
model-path      $TFMODELS
sound-path      $TFMODELS
#endif

window-title Team Fortress
#if $[WINDOWS_PLATFORM]
icon-filename models/gui/tfp2.ico
#elif $[OSX_PLATFORM]
icon-filename models/gui/game.icns
#elif $[UNIX_PLATFORM]
icon-filename models/gui/game.svg
#endif

model-index $TFMODELS/tfmodels_index.boo

load-sounds scripts/game_sounds.txt
load-sounds scripts/game_sounds_footsteps.txt
load-sounds scripts/game_sounds_weapons.txt
load-sounds scripts/game_sounds_player.txt
load-sounds scripts/game_sounds_vo.txt
load-sounds scripts/game_sounds_physics.txt

dc-file $TF/src/configfiles/tf.dc

anim-events $TF/src/configfiles/tf_anim_events.pdx
anim-activities $TF/src/configfiles/tf_anim_activities.pdx

# TF2 on Source runs at 66 ticks per second.
sv_tickrate 66

# Keep hardskinned geometry vertex animated.
# Normally this will convert the hardskinned geometry into
# static geometry and parent it under an expose joint in the
# scene graph, but we want to keep a minimal scene graph and minimize
# draw calls.
egg-rigid-geometry 0
# Don't quantize joint weights, doesn't have any effect for GPU skinning.
egg-vertex-membership-quantize 0.0

# Configuration for cascaded shadow maps.
csm-distance 1600
csm-sun-distance 8000
csm-fixed-film-size #t
csm-border-bias 0.1

# pphysics/PhysX configuration
phys-panda-mass-unit kilograms
phys-panda-length-unit inches
phys-solver pgs
phys-ragdoll-pos-iterations 4
phys-ragdoll-vel-iterations 1
phys-ragdoll-joint-stiffness 0.0
phys-ragdoll-joint-damping 0.0
phys-ragdoll-joint-restitution 0.0
phys-ragdoll-joint-bounce-threshold 0.0
phys-ragdoll-contact-distance-ratio 0.49
phys-ragdoll-projection 1
phys-ragdoll-max-depenetration-vel 10000.0
phys-ragdoll-projection-angular-tolerance 10.0
phys-ragdoll-projection-linear-tolerance 2.0
phys-tolerance-length 0.1
phys-tolerance-speed 20.32

framebuffer-srgb 1

# Postprocessing config.
hdr-enable 0
fxaa-enable 1
ssao-enable 0
motion-blur-enable 0
bloom-enable 0
tone-mapping-enable 1
tone-mapping-algorithm urchima

# FMOD audio configuraton.
# Put this directory on plugin-path.  This is where the Steam Audio
# FMOD plugin should reside.
plugin-path $WINTOOLS/built/bin
fmod-use-steam-audio 1
fmod-speaker-mode stereo
fmod-mixer-sample-rate 48000
fmod-dsp-buffer-size 1024
fmod-number-of-sound-channels 256
fmod-compressed-samples 1
music-volume 1.0
sfx-volume 0.72

# Default viewmodel and normal camera FOVs.
# Taken from original TF2.
viewmodel-fov 54
fov 75

default-cube-map maps/sky.txo

mouse-sensitivity 5

default-near 7.0

interpolate-frames 1

stencil-bits 0

# Allow loading model files without an extension.
default-model-extension .bam

# This is set to the correct release version in the publish config file.
tf-version dev

talker-phoneme-filter 0.08

# Configuration for garbage collection of TransformStates and RenderStates.
# This is essentially the default, but we reduce the number of states collected
# each cycle to reduce overhead.
garbage-collect-states 1
garbage-collect-states-rate 0.01
auto-break-cycles 1
transform-cache 1
state-cache 1

bounds-type box

tf-fast-weapon-switch 0

frame-rate-meter-update-interval 1.0

# Uniquify TextureStages by name.
texture-stage-pool-mode name

# Turn off animation updating during the Cull traversal.
# We do this in App to animate all the characters in parallel,
# and reduce contention on parallel Cull traversals.
cull-animation 0

use-orig-source-shader 1

threading-model /Draw

model-cache-dir tfcache
model-cache-models 0
model-cache-textures 0
model-cache-compiled-shaders 0

# Add specialty bins.
cull-bin decal 29 state_sorted
cull-bin refract 32 state_sorted
cull-bin gui-panel 61 fixed

#end 50_tf.prc

plugin-path .
model-path .
model-path sound

dc-file etc/tf.dc

anim-events etc/tf_anim_events.pdx
anim-activities etc/tf_anim_activities.pdx

# TF2 on Source runs at 66 ticks per second.
sv_tickrate 66

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

load-sounds scripts/game_sounds.txt
load-sounds scripts/game_sounds_footsteps.txt
load-sounds scripts/game_sounds_weapons.txt
load-sounds scripts/game_sounds_player.txt
load-sounds scripts/game_sounds_vo.txt
load-sounds scripts/game_sounds_physics.txt

icon-filename models/gui/game.ico

load-display pandagl

audio-library-name fmod_audio

# OpenGL renderer configurations.
gl-coordinate-system default
gl-version 4 6
gl-compile-and-execute 1
gl-force-depth-stencil 0
gl-force-fbo-color 0
gl-force-no-error 1
gl-force-no-flush 1
gl-force-no-scissor 1
gl-check-errors 0
gl-enable-memory-barriers 0
# This enables OpenGL 4.3+ vertex buffer binding if it's available.
gl-fixed-vertex-attrib-locations 1
gl-immutable-texture-storage 1

# These appear to be old fixed-function and/or munger left overs.
color-scale-via-lighting 0
alpha-scale-via-texture 0

# This makes TransformStates compose by multiplying matrices instead
# of composing the individual transform components, such as pos, hpr,
# and scale.  It is likely to be faster because it is vectorized.
compose-componentwise 0

cache-generated-shaders 0
use-vertex-lit-for-no-material 1

framebuffer-stencil 0
support-stencil 0

rescale-normals none
support-rescale-normal 0

hardware-animated-vertices 1

textures-power-2 none

cull-bin gui-popup 60 unsorted

# Postprocessing config.
hdr-enable 0
ssao-enable 0
bloom-enable 0
tone-mapping-enable 1
tone-mapping-algorithm urchima

# FMOD audio configuration.
fmod-use-steam-audio 1
fmod-speaker-mode stereo
fmod-mixer-sample-rate 48000
fmod-dsp-buffer-size 1024
fmod-number-of-sound-channels 256
fmod-compressed-samples 1
music-volume 1.0
sfx-volume 0.72

default-cube-map maps/sky.txo

default-near 7.0

interpolate-frames 1

stencil-bits 0

# Allow loading model files without an extension.
default-model-extension .bam

tf-version client-alpha

talker-phoneme-filter 0.08

# Configuration for garbage collection of TransformStates and RenderStates.
# This is essentially the default, but we reduce the number of states collected
# each cycle to reduce overhead.
garbage-collect-states 1
garbage-collect-states-rate 0.5
auto-break-cycles 1
transform-cache 1
state-cache 1

bounds-type box

frame-rate-meter-update-interval 1.0

# Uniquify TextureStages by name.
texture-stage-pool-mode name

# Turn off animation updating during the Cull traversal.
# We do this in App to animate all the characters in parallel,
# and reduce contention on parallel Cull traversals.
cull-animation 0

use-orig-source-shader 1

threading-model /Draw
job-system-num-worker-threads 3

model-cache-dir tfcache
model-cache-models 0
model-cache-textures 0
model-cache-compiled-shaders 0

# Add specialty bins.
cull-bin decal 29 state_sorted
cull-bin refract 32 state_sorted
cull-bin gui-panel 61 fixed

#############################################################################
#############################################################################
# Default TF2 options.
# Don't change these, but re-specify them in Config-user.prc

# Set your name in the game.
tf-player-name Player

# Enable/disable fast weapon switch.
tf-fast-weapon-switch 0

# Enable/disable damage numbers.
tf-show-damage-numbers 1

# If 1, skips loading screen and immediately connects to server
# after loading.
tf-play-immediately 0

# IP address of game server to connect to.
client-addr 127.0.0.1

# Enable/disable fullscreen mode.
fullscreen 0
# Set the window size of the game.  Format is <width> <height>.
win-size 1280 720

# Sets the R/G/B color of your crosshair.
cl-crosshair-r 200
cl-crosshair-g 200
cl-crosshair-b 200
# Crosshair alpha.
cl-crosshair-a 255
# Sets the texture of your crosshair.
# Valid crosshairs are crosshair[1-7].
cl-crosshair-file crosshair5
# Sets the size of your crosshair.
cl-crosshair-scale 32

# Sets the resolution of the sun shadows.
# Lower this if your GPU sucks.
shadow-map-size 2048

# Texture filtering settings.
# Change these if your GPU REALLY sucks.
#
# For anisotropic degree, only use these values: 0, 1, 2, 4, 8, or 16
texture-anisotropic-degree 16
# Set minfilter to linear to bilinear filtering.
# Set minfilter to mipmap for trilinear filtering.
# Set both to nearest for Minecraft textures.
texture-minfilter mipmap
texture-magfilter linear

# Enable/disable FXAA antialiasing.  DO NOT use MSAA.
fxaa-enable 1

# Motion blur.
motion-blur-enable 0

# Specify the field-of-view of the viewmodel.
# Currently you cannot change the regular field-of-view.
viewmodel-fov 54
fov 75

# Your mouse sensitivity (maps to original TF2).
mouse-sensitivity 5.0

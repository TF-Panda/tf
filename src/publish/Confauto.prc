plugin-path .
model-path .
model-path sound

# Notify settings
notify-level-gobj warning
notify-level-loader warning
notify-level-material warning
notify-level-prediction warning
notify-timestamp #t

vfs-mount misc.mf .
vfs-mount maps.mf .
vfs-mount materials.mf .
vfs-mount audio.mf .
vfs-mount shaders.mf .
vfs-mount models.mf .
vfs-mount levels.mf .

dc-file etc/tf.dc

anim-events etc/tf_anim_events.pdx
anim-activities etc/tf_anim_activities.pdx

# TF2 on Source runs at 66 ticks per second.
sv_tickrate 66

window-title Team Fortress

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

icon-filename etc/tfp2.ico

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
# NOTE: Broken in update.
gl-immutable-texture-storage 0

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

# Disable tone-mapping by default, as it matches original TF2.
# The available tone-mappers are urchima, aces, and uncharted2.
# In my opinion urchima looks the best, but they all introduce
# a lot of contrast that make the game visually harder to read.
tone-mapping-enable 0
tone-mapping-algorithm urchima
tone-mapping-urchima-contrast 1.0

# FMOD audio configuration.
fmod-use-steam-audio 1
fmod-speaker-mode stereo
fmod-mixer-sample-rate 44100
fmod-dsp-buffer-size 1024
fmod-number-of-sound-channels 256
fmod-compressed-samples 1
fmod-reverb-mix 0.25
fmod-steam-audio-reflection-job 0
fmod-occlusion-db-loss-low -3.0
fmod-occlusion-db-loss-mid -6.0
fmod-occlusion-db-loss-high -9.0
fmod-steam-audio-hrtf-volume 1.0
fmod-steam-audio-normalized-hrtf 0
fmod-clip-output 0
# Reduce volume of spatialized sounds so local player sounds, UI sounds, etc,
# remain clear in the mix.
fmod-spatialized-volume 0.5
music-volume 1.0
sfx-volume 0.72

default-cube-map maps/sky.txo

default-near 7.0

interpolate-frames 1

stencil-bits 0

# Allow loading model files without an extension.
default-model-extension .bam

tf-version alpha

talker-phoneme-filter 0.08

# Configuration for garbage collection of TransformStates and RenderStates.
# This is essentially the default, but we reduce the number of states collected
# each cycle to reduce overhead.
garbage-collect-states 1
garbage-collect-transform-states-rate 0.5
garbage-collect-render-states-rate 0.01
auto-break-cycles 1
transform-cache 0
state-cache 1

bounds-type box

frame-rate-meter-update-interval 0.05

# Uniquify TextureStages by name.
texture-stage-pool-mode name

# Turn off animation updating during the Cull traversal.
# We do this in App to animate all the characters in parallel,
# and reduce contention on parallel Cull traversals.
cull-animation 0
parallel-animation 1

use-orig-source-shader 1

threading-model /Draw
job-system-num-worker-threads 3

model-cache-dir
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

# For servers, do we want a captcha verification to prevent fake
# players?
tf-want-captcha 0

# If 1, skips loading screen and immediately connects to server
# after loading.
tf-play-immediately 0

# IP address of game server to connect to.
client-addr 127.0.0.1

# Enable/disable fullscreen mode.
fullscreen 0
# Set the window size of the game.  Format is <width> <height>.
win-size 1280 720

# V-sync
sync-video 1

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
tf-csm-resolution 2048

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
# Let's use some preferred modern values as default.
viewmodel-fov 54
fov 90

# Your mouse sensitivity (maps to original TF2).
mouse-sensitivity 5.0

# Turn this on to enable water reflections.  It is expensive
# and currently not culled (but the threading helps).
tf-water-reflections 0

# For servers, the map to load on start.
tf-map ctf_2fort

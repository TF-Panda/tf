### Generated automatically by ppremake 1.25 from tf.prc.pp.
################################ DO NOT EDIT ###########################

model-path      $TFMODELS/built
sound-path      $TFMODELS/built

window-title Team Fortress
icon-filename models/gui/game.ico

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

egg-rigid-geometry 0

csm-distance 1000
csm-sun-distance 4000

phys-tolerance-length 1
phys-tolerance-speed 20.32
phys-panda-mass-unit kilograms
phys-panda-length-unit inches
phys-enable-pvd #f
phys-enable-pvd-server #t
phys-solver tgs
phys-ragdoll-contact-distance-ratio 0.5
phys-ragdoll-projection-angular-tolerance 15.0
phys-ragdoll-projection-linear-tolerance 8.0
phys-ragdoll-max-depenetration-vel 5.0
phys-ragdoll-projection 0
phys-ragdoll-pos-iterations 8
phys-ragdoll-vel-iterations 4

framebuffer-srgb 1

hbao-falloff 2.0
hbao-max-sample-distance 20.0
hbao-sample-radius 3.5
hbao-angle-bias 0.564
hbao-strength 5.0

hdr-enable 1
fxaa-enable 0
ssao-enable 0
motion-blur-enable 0
mat_motion_blur_forward_enabled 1
tone-mapping-algorithm urchima

bloom-enable 0
bloom-remove-fireflies false
bloom-strength-1 0.8
bloom-strength-2 1
bloom-strength-3 1
bloom-strength-4 1
bloom-strength-5 1
bloom-radius-5 1
bloom-radius-4 1
bloom-radius-3 1
bloom-radius-2 1
bloom-radius-1 1
bloom-streak-length 1
bloom-blur-passes 5
bloom-luminance-threshold 1.0

hdr-max-shutter 30
hdr-min-aperature 3.5
hdr-max-iso 12800
hdr-exposure-method 1
hdr-max-ev 15.99
hdr-exposure-std-middle-grey 0.5
hdr-luminance-buffers 4

shadow-depth-bits 24

fmod-speaker-mode stereo
fmod-audio-preload-threshold -1
fmod-mixer-sample-rate 44100

viewmodel-fov 54
fov 90

default-cube-map maps/sky.txo

mouse-sensitivity 5

default-near 7.0

interpolate-frames 1

stencil-bits 0

# Allow loading model files without an extension.
default-model-extension .bam

# This is set to the correct release version in the publish config file.
tf-version dev


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
sound-path      $TFMODELS/built
#else
// Most people outside the VR Studio just see this.
model-path      $TFMODELS
sound-path      $TFMODELS
#endif

window-title Team Fortress
#if $[WINDOWS_PLATFORM]
icon-filename models/gui/game.ico
#elif $[OSX_PLATFORM]
icon-filename models/gui/game.icns
#elif $[UNIX_PLATFORM]
icon-filename models/gui/game.svg
#endif

dc-file $TF/src/configfiles/tf.dc

anim-events $TF/src/configfiles/tf_anim_events.pdx
anim-activities $TF/src/configfiles/tf_anim_activities.pdx

# TF2 on Source runs at 66 ticks per second.
sv_tickrate 66

#end 50_tf.prc

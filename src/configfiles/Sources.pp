#define INSTALL_CONFIG \
  $[ODIR_GEN]/50_tf.prc

#if $[CTPROJS]
  // These files only matter to ctattach users.
  #define INSTALL_CONFIG $[INSTALL_CONFIG] tf.init
#endif

#include $[THISDIRPREFIX]tf.prc.pp

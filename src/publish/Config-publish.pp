//
// Config.pp
//
// This file configures a publish build for TF.
//

#define LANGUAGE english

// Compile with optimize level 4.  This is the "release" optimize
// level.  Full compiler optimizations, no asserts, no memory tracking,
// no debug symbols, no PStats.
#define OPTIMIZE 4
#define DO_MEMORY_USAGE

// Only look for prc files in the etc directory of the root
// game installation directory.
#define DEFAULT_PRC_DIR ./etc/
#define PRC_PATTERNS *.prc
#define PRC_DIR_ENVVARS
#define PRC_PATH_ENVVARS

#define USE_MEMORY_MIMALLOC 1
#define DO_PIPELINING 1
#define USE_DELETED_CHAIN
#define LINMATH_ALIGN 1
#define ARCH_FLAGS /arch:SSE2
#define BUILD_COMPONENTS 1
#define DONT_COMPOSITE 1
#define DO_CROSSOBJ_OPT 1
#define MSBUILD_PLATFORM_TOOLSET v143

// We don't need the egg tools in a publish build.
#define HAVE_EGG
#define HAVE_EIGEN
#define HAVE_MAYA
#define HAVE_DX9
#define HAVE_BULLET
#define HAVE_ODE
#define HAVE_OIDN
#define HAVE_VORBIS
#define HAVE_ASSIMP
#define HAVE_JPEG
#define HAVE_PNG
#define HAVE_TIFF
#define HAVE_OPENAL
#define HAVE_SQUISH
#define HAVE_ZLIB

// Now include the platform-specific Config.pp file if it exists.
#sinclude $[THISDIRPREFIX]Config-publish.$[PLATFORM].pp

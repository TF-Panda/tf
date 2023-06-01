//
// Config.pp
//
// This file configures a publish build for TF on the Windows platform.
//

//
// Define third-party package locations.
// These are the same as a developer build, but with certain packages
// excluded that we don't need in a publish.
//
#define EMBREE_IPATH $[WINTOOLS]/built/embree/include
#define EMBREE_LPATH $[WINTOOLS]/built/embree/lib

#define FREETYPE_IPATH $[WINTOOLS]/built/freetype/include/freetype2
#define FREETYPE_LPATH $[WINTOOLS]/built/freetype/lib

#define VALVE_STEAMNET_IPATH $[WINTOOLS]/built/gamenetworkingsockets/include/GameNetworkingSockets
#define VALVE_STEAMNET_LPATH $[WINTOOLS]/built/gamenetworkingsockets/lib

#define GLSLANG_IPATH $[WINTOOLS]/built/glslang/include
#define GLSLANG_LPATH $[WINTOOLS]/built/glslang/lib

#define HARFBUZZ_IPATH $[WINTOOLS]/built/harfbuzz/include
#define HARFBUZZ_LPATH $[WINTOOLS]/built/harfbuzz/lib

#define OPENSSL_IPATH $[WINTOOLS]/built/openssl/include
#define OPENSSL_LPATH $[WINTOOLS]/built/openssl/lib

#define SPIRV_CROSS_IPATH $[WINTOOLS]/built/spirv-cross/include
#define SPIRV_CROSS_LPATH $[WINTOOLS]/built/spirv-cross/lib

#define SPIRV_TOOLS_IPATH $[WINTOOLS]/built/spirv-tools/include
#define SPIRV_TOOLS_LPATH $[WINTOOLS]/built/spirv-tools/lib

#define MIMALLOC_IPATH $[WINTOOLS]/built/mimalloc/include
#define MIMALLOC_LPATH $[WINTOOLS]/built/mimalloc/lib

#define FMOD_IPATH $[WINTOOLS]/built/fmod/include
#define FMOD_LPATH $[WINTOOLS]/built/fmod/lib

#define PHYSX_IPATH $[WINTOOLS]/built/physx/include
#define PHYSX_LPATH $[WINTOOLS]/built/physx/lib

#define STEAM_AUDIO_IPATH $[WINTOOLS]/built/steamaudio/include
#define STEAM_AUDIO_LPATH $[WINTOOLS]/built/steamaudio/lib

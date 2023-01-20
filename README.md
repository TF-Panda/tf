# tf
This is the code tree for TF2 Panda.  It contains all of the game code and configuration files.  It is mostly Python, with some of the client-side prediction system being written in C++ as a performance optimization.

The game is still a work-in-progress.

In order for gameplay mechanics to be as accurate as possible, a lot of the code from original TF2 was used as reference.

The game cannot be run from this repository as-is -- it must be built against the rest of the engine using its build system, and integrated into the development environment.  The engine is a collection of separate repositories, which are available [here](https://github.com/toontownretro).  Instructions for setting up the development environment and building the engine is available in the wiki of the documentation repository.

The assets for the game are stored in a separate repository: [tfmodels](https://github.com/TF-Panda/tfmodels)

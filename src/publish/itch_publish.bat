@echo off

call cta tf
call cta pandatool

set INSTALL_DIR=%PLAYER%\tf-install
set PERSIST_DIR=%PLAYER%\tf-publish

python %TF%\src\publish\QuickScrubber.py -p WIN32 -f %TF%\src\publish\QuickFilelist.txt scrub %INSTALL_DIR% %PERSIST_DIR%
python %TF%\src\publish\QuickScrubber.py -p WIN32 -f %TF%\src\publish\QuickFilelist.txt copy %INSTALL_DIR% %PERSIST_DIR%

cd %INSTALL_DIR%
butler push . lachb/tf2p:win64-devel

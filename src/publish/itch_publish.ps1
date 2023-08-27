cta tf
cta pandatool

$INSTALL_DIR="$HOME/tf-install"
$PERSIST_DIR="$HOME/tf-publish"

python $env:TF\src\publish\QuickScrubber.py -p WIN32 -f $env:TF\src\publish\QuickFilelist.txt scrub $INSTALL_DIR $PERSIST_DIR
python $env:TF\src\publish\QuickScrubber.py -p WIN32 -f $env:TF\src\publish\QuickFilelist.txt copy $INSTALL_DIR $PERSIST_DIR

set-location $INSTALL_DIR
butler push . lachb/tf2p:win64-devel

#import pyjion
#pyjion.enable()

#
# Original bootstrap logger that gets LOGGING IMMEDIATELY UP before any
# Panda/Toontown dependencies are imported
#
if 1:   # flip this as necessary
    # Setup the log files
    # We want C++ and Python to both go to the same log so they
    # will be interlaced properly.

    import time
    import sys
    import os

    if not os.path.isdir("logs"):
        os.mkdir("logs")

    # match log format specified in installerBase.cxx,
    # want this fmt so log files can be sorted oldest first based on name,
    # and so old open handles to logs dont prevent game from starting
    ltime = time.localtime()
    if __debug__:
        logSuffix = "dev-%02d%02d%02d_%02d%02d%02d" % (ltime[0]-2000,ltime[1],ltime[2],ltime[3],ltime[4],ltime[5])
    else:
        logSuffix = "%02d%02d%02d_%02d%02d%02d" % (ltime[0]-2000,ltime[1],ltime[2],ltime[3],ltime[4],ltime[5])
    logfile = 'logs' + os.path.sep + 'teamfortress-' + logSuffix + '.log'

    # Redirect Python output and err to the same file
    class LogAndOutput:
        def __init__(self, orig, log):
            self.orig = orig
            self.log = log
        def write(self, str):
            self.log.write(str)
            self.log.flush()
            self.orig.write(str)
            self.orig.flush()
        def flush(self):
            self.log.flush()
            self.orig.flush()

    # old game log deletion now managed by activeX control
    ## Delete old log files so they do not clog up the disk
    ##if os.path.exists(logfile):
    ##    os.remove(logfile)

    # Open the new one for appending
    # Make sure you use 'a' mode (appending) because both Python and
    # Panda open this same filename to write to. Append mode has the nice
    # property of seeking to the end of the output stream before actually
    # writing to the file. 'w' mode does not do this, so you will see Panda
    # output and Python output not interlaced properly.
    log = open(logfile, 'a')
    logOut = LogAndOutput(sys.__stdout__, log)
    logErr = LogAndOutput(sys.__stderr__, log)
    sys.stdout = logOut
    sys.stderr = logErr

    # Give Panda the same log we use
    if True:#__debug__:
        from panda3d.core import Notify, Filename, MultiplexStream
        nout = MultiplexStream()
        Notify.ptr().setOstreamPtr(nout, 0)
        nout.addFile(Filename(logfile))
        nout.addStandardOutput()
        nout.addSystemDebug()

    # Write to the log
    print("\n\nStarting Team Fortress...")
    print(("Current time: " + time.asctime(time.localtime(time.time()))
           + " " + time.tzname[0]))
    print("sys.path = ", sys.path)
    print("sys.argv = ", sys.argv)
    print("os.environ = ", os.environ)

import argparse
p = argparse.ArgumentParser(description='Team Fortress Entry-Point')
p.add_argument('-s', '--server', help='Launch a server instance instead of a client.', action='store_true', default=False, required=False)
p.add_argument('-p', '--port', help='Port number when launching a server instance.', type=int, default=-1, required=False)
args = p.parse_args()

print('TFStart: Starting the game.')

import builtins
# Add a builtin variable indicating whether or not this is a client instance.
# This is used by shared code to differentiate between client and server.
builtins.IS_CLIENT = (not args.server)

from panda3d.core import *

if args.server:
    print('TFStart: Running server instance.')
    if args.port != -1:
        loadPrcFileData("cmd args", "sv_port %i" % args.port)
    from tf.tfbase.TFServerBase import TFServerBase
    base = TFServerBase()
else:
    print('TFStart: Running client instance.')
    from tf.tfbase.TFBase import TFBase
    base = TFBase()
    base.request("Intro")
base.run()

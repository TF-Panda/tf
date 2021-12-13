#import pyjion
#pyjion.enable()

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
